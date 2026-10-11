import io
import json
import threading
import time
from urllib.error import HTTPError

import pytest
from fastapi.testclient import TestClient

from app.gemini import GeminiProvider
from app.main import SAMPLES, create_app
from app.parsing import parse_logs
from app.repository import Repository
from app.schemas import ModelReport, validate_references
from tests.test_core import MockIndex, MockProvider, login, settings, wait_job


def test_throttle_is_bounded_and_each_attempt_uses_budget(tmp_path, monkeypatch):
    cfg = settings(tmp_path, max_model_calls=3, gemini_api_key="mock-only")
    repo = Repository(cfg)
    provider = GeminiProvider(cfg, repo)
    monkeypatch.setattr("app.gemini.time.sleep", lambda _: None)
    calls = []

    def throttled(request, timeout):
        calls.append(1)
        raise HTTPError(request.full_url, 429, "Limited", {}, io.BytesIO(b"{}"))

    monkeypatch.setattr("app.gemini.urlopen", throttled)
    with pytest.raises(RuntimeError, match="HTTP 429"):
        provider.request("mock-only", "generateContent", {})
    assert len(calls) == 2
    monkeypatch.setattr("app.gemini.urlopen", lambda *a, **k: io.BytesIO(b"{}"))
    provider.request("mock-only", "generateContent", {})
    with pytest.raises(RuntimeError, match="limit reached"):
        provider.request("mock-only", "generateContent", {})


def test_access_denied_is_not_retried(tmp_path, monkeypatch):
    provider = GeminiProvider(
        settings(tmp_path, gemini_api_key="mock-only"), Repository(settings(tmp_path))
    )
    calls = []

    def denied(request, timeout):
        calls.append(1)
        raise HTTPError(request.full_url, 403, "Denied", {}, io.BytesIO(b"{}"))

    monkeypatch.setattr("app.gemini.urlopen", denied)
    with pytest.raises(RuntimeError, match="HTTP 403"):
        provider.request("mock-only", "generateContent", {})
    assert len(calls) == 1


@pytest.mark.parametrize("status", ["no_incident_detected", "insufficient_evidence"])
def test_uncertainty_contract(status):
    report = ModelReport.model_validate(
        {
            "title": "No supported cause",
            "summary": "More context may be needed.",
            "analysis_status": status,
            "observed_facts": [],
            "timeline": [],
            "hypotheses": [],
            "recommended_checks": [],
            "recovery_guidance": [],
            "limitations": ["This excerpt does not establish system-wide health."],
        }
    )
    validate_references(report, parse_logs("request failed"), [])


def test_queue_limit_and_late_timeout_does_not_resurrect(tmp_path):
    gate = threading.Event()

    class Slow(MockProvider):
        def embed(self, text):
            gate.wait(0.3)
            return super().embed(text)

    app = create_app(
        settings(tmp_path, queue_size=1, investigation_timeout_seconds=0), Slow(), MockIndex()
    )
    with TestClient(app) as client:
        headers = login(client)
        first = client.post(
            "/api/incidents", json={"text": SAMPLES[0]["text"]}, headers=headers
        ).json()["id"]
        terminal = wait_job(client, first)
        assert terminal["error"]["code"] == "timeout"
        second = client.post("/api/incidents", json={"text": SAMPLES[0]["text"]}, headers=headers)
        assert second.status_code == 202
        assert (
            client.post(
                "/api/incidents", json={"text": SAMPLES[0]["text"]}, headers=headers
            ).status_code
            == 429
        )
        gate.set()
        time.sleep(0.06)
        assert client.get("/api/incidents/" + first).json()["status"] == "failed"


def test_completed_history_survives_restart(tmp_path):
    cfg = settings(tmp_path)
    with TestClient(create_app(cfg, MockProvider(), MockIndex())) as client:
        headers = login(client)
        identifier = client.post(
            "/api/incidents", json={"text": SAMPLES[0]["text"]}, headers=headers
        ).json()["id"]
        assert wait_job(client, identifier)["status"] == "completed"
        cookie = client.cookies.get("cloudlens_session")
    with TestClient(create_app(cfg, MockProvider(), MockIndex())) as restarted:
        restarted.cookies.set("cloudlens_session", cookie)
        assert restarted.get("/api/incidents").json()["total"] == 1
        result = restarted.get("/api/incidents/" + identifier).json()
        assert result["status"] == "completed"
        assert "synthetic-secret" not in json.dumps(result)
