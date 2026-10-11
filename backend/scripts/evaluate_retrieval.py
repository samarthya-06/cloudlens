"""Twelve labelled queries against the real cached embedding index."""

import json
from pathlib import Path

from app.config import Settings
from app.provider import create_provider
from app.repository import Repository
from app.retrieval import VectorIndex

CASES = [
    ("PostgreSQL password authentication failed for app_user", "DB-AUTH"),
    ("role cannot log in after changing database credentials", "DB-AUTH"),
    ("database connection refused at host port 5432", "DB-NET"),
    ("cannot resolve database hostname", "DB-NET"),
    ("missing required environment variable DATABASE_URL at startup", "APP-ENV"),
    ("PutObject AccessDenied while uploading to S3", "S3-DENY"),
    ("httpx.ReadTimeout waiting for catalog upstream response", "HTTP-TIME"),
    ("container OOMKilled and out of memory", "MEMORY"),
    ("No space left on device during log write", "DISK"),
    ("nginx upstream prematurely closed connection 502", "PROXY"),
    ("Alembic migration revision not found during startup", "STARTUP"),
    ("external API TooManyRequests 429 retry limit", "THROTTLE"),
]


def main():
    settings = Settings()
    index = VectorIndex(settings)
    index.load()
    provider = create_provider(settings, Repository(settings))
    rows = []
    for query, expected in CASES:
        chunks, _ = index.retrieve(provider.embed(query), 3)
        actual = [c.runbook_id for c in chunks]
        rows.append(
            {"query": query, "expected": expected, "top3": actual, "hit": expected in actual}
        )
    hits = sum(r["hit"] for r in rows)
    result = {
        "live_embeddings": True,
        "hits": hits,
        "total": len(rows),
        "hit_at_3": hits / len(rows),
        "cases": rows,
    }
    Path("../docs/evidence/runtime/retrieval.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    if hits < 10:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
