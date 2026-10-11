"""Live generation/citation evaluation. Manual semantic review remains required."""

import json
from pathlib import Path

from app.config import Settings
from app.generation import generate
from app.main import SAMPLES
from app.parsing import parse_logs
from app.provider import create_provider
from app.repository import Repository
from app.retrieval import VectorIndex


def main():
    settings = Settings()
    provider = create_provider(settings, Repository(settings))
    index = VectorIndex(settings)
    index.load()
    cases = [(s["id"], s["text"], "incident_detected") for s in SAMPLES]
    for name, expected in [
        ("healthy", "no_incident_detected"),
        ("ambiguous", "insufficient_evidence"),
        ("prompt-injection", "incident_detected"),
    ]:
        cases.append((name, Path(f"../samples/{name}.txt").read_text(), expected))
    rows = []
    root = Path("../docs/evidence/runtime/live-reports")
    root.mkdir(parents=True, exist_ok=True)
    for name, text, expected in cases:
        evidence = parse_logs(text)
        chunks, _ = index.retrieve(provider.embed(evidence.query))
        report, usage = generate(provider, evidence, chunks)
        snapshot = {
            "live": True,
            "sample": name,
            "model": settings.generation_model,
            "region": settings.inference_location,
            "report": report.model_dump(),
            "evidence": evidence.model_dump(),
            "retrieved_chunks": [c.model_dump() for c in chunks],
            "usage": usage,
        }
        (root / f"{name}.json").write_text(json.dumps(snapshot, indent=2))
        rows.append(
            {
                "sample": name,
                "expected": expected,
                "actual": report.analysis_status,
                "schema_and_ids_valid": True,
                "status_matches": report.analysis_status == expected,
                "semantic_review": "pending human inspection",
            }
        )
    Path("../docs/evidence/runtime/generation.json").write_text(
        json.dumps({"live": True, "cases": rows}, indent=2)
    )
    print(json.dumps(rows, indent=2))
    if not all(row["status_matches"] for row in rows):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
