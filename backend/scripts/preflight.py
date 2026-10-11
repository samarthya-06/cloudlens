"""Small real Gemini probes; never display the private API key."""

import json
from pathlib import Path

from app.config import Settings
from app.provider import create_provider
from app.repository import Repository


def main():
    settings = Settings()
    provider = create_provider(settings, Repository(settings))
    result = {
        "provider": "gemini",
        "generation_model": settings.generation_model,
        "embedding_model": settings.embedding_model_id,
        "dimensions": settings.embedding_dimensions,
    }
    try:
        vector = provider.embed("Synthetic database authentication failure.")
        result["embedding_verified"] = len(vector) == settings.embedding_dimensions
        text, usage = provider.converse(
            "Return a JSON object with an explanation field.", "Explain application logs briefly."
        )
        result["generation_verified"] = bool(json.loads(text))
        result["usage"] = usage
    except (RuntimeError, ValueError, TimeoutError) as exc:
        result["error_type"] = type(exc).__name__
        result["generation_verified"] = False
    destination = Path("../docs/evidence/runtime/gemini-probe.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result.get("generation_verified") and result.get("embedding_verified") else 1


if __name__ == "__main__":
    raise SystemExit(main())
