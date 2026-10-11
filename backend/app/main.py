import asyncio
import hashlib
import json
import logging
import secrets
import time
import uuid
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import Settings
from app.gemini import GeminiServiceError
from app.generation import generate
from app.parsing import decode_input, parse_logs, redact
from app.provider import create_provider
from app.repository import Repository
from app.retrieval import VectorIndex
from app.storage import ArtifactStore, markdown_report

logger = logging.getLogger("cloudlens")
logging.basicConfig(level=logging.INFO, format="%(message)s")
SAMPLES = [
    {
        "id": "database",
        "title": "Database authentication",
        "description": "A deployment precedes authentication failures. Credential mismatch is unconfirmed.",
        "filename": "deployment-db.log",
        "text": "2026-10-11T14:02:00Z INFO deploy v1.8 completed\n2026-10-11T14:02:01Z INFO connecting as app_user\n2026-10-11T14:02:01Z INFO password=synthetic-secret\n2026-10-11T14:02:03Z ERROR password authentication failed for user app_user\nTraceback (most recent call last):\n    psycopg.OperationalError: authentication failed\n2026-10-11T14:02:05Z ERROR password authentication failed for user app_user\n2026-10-11T14:02:05Z WARN /health returned 503",
    },
    {
        "id": "s3",
        "title": "S3 access denied",
        "description": "An upload returns AccessDenied. Policy evidence is needed.",
        "filename": "s3-access.log",
        "text": "2026-10-11T13:50:00Z INFO starting synthetic report upload\n2026-10-11T13:50:01Z ERROR PutObject returned AccessDenied for s3://synthetic-bucket/reports/demo.json\n    botocore.exceptions.ClientError: AccessDenied\n2026-10-11T13:50:02Z WARN report upload failed; local copy retained",
    },
    {
        "id": "timeout",
        "title": "Upstream timeouts",
        "description": "Repeated requests time out. CPU overload needs metrics.",
        "filename": "upstream-timeout.log",
        "text": "2026-10-11T13:28:00Z INFO GET /catalog started\n2026-10-11T13:28:30Z ERROR upstream request timed out after 30s\n    httpx.ReadTimeout: waiting for catalog service\n2026-10-11T13:28:31Z WARN GET /catalog returned 504\n2026-10-11T13:29:01Z ERROR upstream request timed out after 30s",
    },
]


class Login(BaseModel):
    password: str = Field(max_length=256)


def create_app(settings: Settings | None = None, provider=None, index=None) -> FastAPI:
    settings = settings or Settings()
    repository = Repository(settings)
    provider = provider or create_provider(settings, repository)
    index = index or VectorIndex(settings)
    storage = ArtifactStore(settings)
    queue: asyncio.Queue = asyncio.Queue(maxsize=settings.queue_size)
    pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cloudlens")
    login_attempts = defaultdict(deque)

    def process(identifier: str):
        started = time.monotonic()
        current = repository.get(identifier)
        from app.schemas import Evidence

        evidence = Evidence.model_validate(current["evidence"])
        index.load()  # fail early before spending a query embedding call
        vector = provider.embed(evidence.query)
        chunks, metadata = index.retrieve(vector)
        retained = {
            "synthetic": current.get("synthetic", False),
            "filename": current["filename"],
            "evidence": evidence.model_dump(),
            "retrieved_chunks": [c.model_dump() for c in chunks],
        }
        repository.update(identifier, "processing", retained)
        if repository.get(identifier)["status"] == "failed":
            raise RuntimeError("Investigation deadline elapsed before generation.")
        report, usage = generate(provider, evidence, chunks)
        payload = retained | {
            "report": report.model_dump()
            | {
                "incident_id": identifier,
                "sources": [
                    {"id": c.id, "title": c.title, "source_urls": c.source_urls} for c in chunks
                ],
            },
            "details": {
                "model_id": settings.generation_model,
                "ai_provider": settings.ai_provider,
                "embedding_model": settings.embedding_model_id,
                "inference_location": settings.inference_location,
                "index_version": metadata["version"],
                "duration_seconds": round(time.monotonic() - started, 2),
                "usage": usage,
            },
        }
        return payload

    async def worker():
        loop = asyncio.get_running_loop()
        while True:
            identifier = await queue.get()
            current = repository.get(identifier)
            retained = {k: current[k] for k in ["filename", "evidence", "synthetic"]}
            repository.update(identifier, "processing", retained)
            future = loop.run_in_executor(pool, process, identifier)
            try:
                payload = await asyncio.wait_for(
                    asyncio.shield(future), settings.investigation_timeout_seconds
                )
                artifact = await loop.run_in_executor(pool, storage.save, identifier, payload)
                payload["artifact"] = artifact
                repository.update(identifier, "completed", payload)
                logger.info(
                    json.dumps(
                        {
                            "event": "investigation",
                            "incident_id": identifier,
                            "outcome": "completed",
                            **payload["details"],
                        }
                    )
                )
            except Exception as exc:
                current = repository.get(identifier)
                retained = {
                    k: current[k]
                    for k in ["filename", "evidence", "synthetic", "retrieved_chunks"]
                    if k in current
                }
                code = "generation_failed"
                message = "Analysis failed. Your redacted evidence is available. Retry after checking service access."
                if isinstance(exc, TimeoutError):
                    code, message = (
                        "timeout",
                        "The investigation timed out. Evidence is retained; retry creates a new investigation.",
                    )
                elif isinstance(exc, ValueError):
                    code, message = (
                        "invalid_report",
                        "Report validation failed. Unsupported evidence references are not displayed.",
                    )
                elif isinstance(exc, GeminiServiceError):
                    code = "provider_error"
                    message = "The AI service could not complete this request. Your redacted evidence is retained. Try again shortly."
                    if exc.status == 429:
                        message = "The AI service usage limit was reached. Your redacted evidence is retained. Wait before retrying."
                elif isinstance(exc, RuntimeError):
                    code = "setup_required"
                    message = "Analysis is unavailable until the presenter completes service setup. Your redacted evidence remains available."
                    if str(exc).startswith("Demo model-call limit reached"):
                        message = "The demo model-call limit has been reached. Ask the presenter to review usage."
                elif isinstance(exc, (BotoCoreError, ClientError)):
                    code = "provider_error"
                retained["error"] = {"code": code, "message": message}
                repository.update(identifier, "failed", retained)
                logger.info(
                    json.dumps(
                        {
                            "event": "investigation",
                            "incident_id": identifier,
                            "outcome": "failed",
                            "error_code": code,
                        }
                    )
                )
                # An SDK thread cannot be cancelled. Hold this worker until it finishes;
                # never save its late result and never overlap another generation.
                if not future.done():
                    try:
                        await asyncio.shield(future)
                    except Exception:
                        pass
            finally:
                queue.task_done()

    @asynccontextmanager
    async def lifespan(app):
        repository.recover()
        task = asyncio.create_task(worker())
        yield
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        pool.shutdown(wait=False, cancel_futures=True)

    app = FastAPI(title="CloudLens", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.state.repository = repository

    @app.middleware("http")
    async def request_controls(request: Request, call_next):
        request_id = uuid.uuid4().hex
        started = time.monotonic()
        if request.method in {"POST", "DELETE", "PUT", "PATCH"}:
            if request.headers.get("origin") not in settings.origins:
                return JSONResponse({"detail": "Request origin is not allowed."}, status_code=403)
            # Bound raw request bytes as well as decoded log bytes (JSON escape overhead).
            parts, size = [], 0
            async for part in request.stream():
                size += len(part)
                if size > settings.max_upload_bytes * 6 + 65536:
                    return JSONResponse({"detail": "Request is too large."}, status_code=413)
                parts.append(part)
            request._body = b"".join(parts)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        logger.info(
            json.dumps(
                {
                    "event": "request",
                    "request_id": request_id,
                    "method": request.method,
                    "status": response.status_code,
                    "duration_ms": round((time.monotonic() - started) * 1000),
                }
            )
        )
        return response

    def session(request: Request):
        value = repository.session(request.cookies.get("cloudlens_session"))
        if not value:
            raise HTTPException(401, "Enter the demo workspace to continue.")
        if request.method in {"POST", "DELETE", "PUT", "PATCH"} and not secrets.compare_digest(
            request.headers.get("x-csrf-token", "").encode(), value["csrf"].encode()
        ):
            raise HTTPException(403, "Session validation failed. Reload and try again.")
        return value

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.post("/api/session")
    def login(body: Login, request: Request, response: Response):
        key = request.client.host if request.client else "unknown"
        attempts = login_attempts[key]
        while attempts and attempts[0] < time.monotonic() - 60:
            attempts.popleft()
        if len(attempts) >= 10:
            raise HTTPException(429, "Too many attempts. Wait a minute and try again.")
        attempts.append(time.monotonic())
        if not settings.demo_password or len(settings.session_secret) < 32:
            raise HTTPException(503, "The presenter must configure demo access first.")
        if not secrets.compare_digest(
            hashlib.sha256(body.password.encode()).digest(),
            hashlib.sha256(settings.demo_password.encode()).digest(),
        ):
            raise HTTPException(401, "That password didn’t match. Try again.")
        token, csrf = repository.create_session()
        response.set_cookie(
            "cloudlens_session",
            token,
            httponly=True,
            secure=settings.cookie_secure,
            samesite="strict",
            max_age=86400,
        )
        return {"csrf_token": csrf}

    @app.get("/api/session")
    def current_session(value=Depends(session)):
        return {"csrf_token": value["csrf"]}

    @app.delete("/api/session")
    def logout(response: Response, value=Depends(session)):
        repository.logout(value["id"])
        response.delete_cookie(
            "cloudlens_session", secure=settings.cookie_secure, httponly=True, samesite="strict"
        )
        return {"status": "logged_out"}

    @app.get("/api/samples")
    def samples(value=Depends(session)):
        return [{**sample, "synthetic": True} for sample in SAMPLES]

    @app.post("/api/incidents", status_code=202)
    async def investigate(request: Request, value=Depends(session)):
        if queue.full():
            raise HTTPException(429, "The demo queue is full. Try again after a job finishes.")
        if repository.history(value["id"], 1)["total"] >= settings.max_session_analyses:
            raise HTTPException(429, "This session has reached its investigation limit.")
        filename = "Pasted logs"
        try:
            if request.headers.get("content-type", "").startswith("multipart/form-data"):
                form = await request.form(
                    max_files=1, max_fields=2, max_part_size=settings.max_upload_bytes
                )
                upload = form.get("file")
                if (
                    not upload
                    or not hasattr(upload, "filename")
                    or not upload.filename.lower().endswith((".txt", ".log"))
                ):
                    raise ValueError("Choose a UTF-8 .txt or .log file.")
                data = await upload.read(settings.max_upload_bytes + 1)
                filename = upload.filename.replace("\\", "/").split("/")[-1][:160]
                filename, _ = redact(filename)
            elif request.headers.get("content-type", "").startswith("application/json"):
                body = await request.json()
                if not isinstance(body, dict) or not isinstance(body.get("text"), str):
                    raise ValueError("Provide pasted logs as text.")
                data = body["text"].encode()
            else:
                raise ValueError("Use the log upload or paste form.")
            text = decode_input(data, settings.max_upload_bytes)
        except (ValueError, UnicodeError) as exc:
            raise HTTPException(422, str(exc)) from exc
        evidence = parse_logs(text)
        if queue.full():
            raise HTTPException(429, "The demo queue is full. Try again later.")
        if repository.history(value["id"], 1)["total"] >= settings.max_session_analyses:
            raise HTTPException(429, "This session has reached its investigation limit.")
        identifier = uuid.uuid4().hex
        repository.create(
            identifier,
            value["id"],
            "Investigation in progress",
            {
                "filename": filename,
                "evidence": evidence.model_dump(),
                "synthetic": any(text == item["text"] for item in SAMPLES),
            },
        )
        queue.put_nowait(identifier)
        return {"id": identifier, "status": "queued"}

    @app.get("/api/incidents")
    def history(page: int = Query(1, ge=1, le=10000), value=Depends(session)):
        return repository.history(value["id"], page)

    def owned(identifier: str, value):
        incident = repository.get(identifier, value["id"])
        if not incident:
            raise HTTPException(404, "Investigation not found in this session.")
        return incident

    @app.get("/api/incidents/{identifier}")
    def detail(identifier: str, value=Depends(session)):
        return owned(identifier, value)

    @app.get("/api/incidents/{identifier}/download")
    def download(
        identifier: str, format: str = Query("md", pattern="^(md|json)$"), value=Depends(session)
    ):
        incident = owned(identifier, value)
        if incident["status"] != "completed":
            raise HTTPException(409, "A validated report is not available yet.")
        content = (
            markdown_report(incident)
            if format == "md"
            else json.dumps(incident, ensure_ascii=False, indent=2)
        )
        return Response(
            content,
            media_type="text/markdown" if format == "md" else "application/json",
            headers={
                "Content-Disposition": f'attachment; filename="cloudlens-{incident["id"]}.{format}"'
            },
        )

    return app


app = create_app()
