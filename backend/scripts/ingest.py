"""Build an app-owned vector snapshot from project runbooks using real Gemini embeddings."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from app.config import Settings
from app.provider import create_provider
from app.repository import Repository
from app.retrieval import INDEX_VERSION, chunk_runbooks


def main():
    settings = Settings()
    provider = create_provider(settings, Repository(settings))
    chunks = chunk_runbooks(Path("../knowledge/runbooks"))
    if not 8 <= len({c.runbook_id for c in chunks}) <= 10:
        raise SystemExit("Expected 8–10 original project runbooks.")
    root = settings.index_path
    root.mkdir(parents=True, exist_ok=True)
    cache = root / "cache"
    cache.mkdir(exist_ok=True)
    config = {
        "model": settings.embedding_model_id,
        "dimensions": settings.embedding_dimensions,
        "normalize": True,
        "region": settings.inference_location,
        "version": INDEX_VERSION,
    }
    vectors = []
    calls = 0
    for chunk in chunks:
        digest = hashlib.sha256(
            (chunk.content_hash + json.dumps(config, sort_keys=True)).encode()
        ).hexdigest()
        path = cache / f"{digest}.npy"
        if path.exists():
            vector = np.load(path, allow_pickle=False)
        else:
            vector = provider.embed(chunk.text)
            np.save(path, vector, allow_pickle=False)
            calls += 1
        if vector.shape != (settings.embedding_dimensions,) or not np.isfinite(vector).all():
            raise ValueError("Cached embedding is invalid")
        vectors.append(vector)
    # Publish metadata last so incomplete builds cannot look like a complete snapshot.
    serialized = json.dumps([c.model_dump() for c in chunks], ensure_ascii=False, indent=2).encode()
    (root / "chunks.json").write_bytes(serialized)
    np.savez_compressed(root / "index.npz", vectors=np.stack(vectors))
    metadata = config | {
        "built_at": datetime.now(UTC).isoformat(),
        "chunks": len(chunks),
        "chunks_sha256": hashlib.sha256(serialized).hexdigest(),
        "live_embedding_calls": calls,
    }
    (root / "metadata.json").write_text(json.dumps(metadata, indent=2))
    if settings.s3_bucket:
        import boto3

        client = boto3.Session(profile_name=settings.aws_profile).client(
            "s3", region_name=settings.aws_region
        )
        for name in ["chunks.json", "index.npz", "metadata.json"]:
            client.put_object(
                Bucket=settings.s3_bucket,
                Key=f"{settings.s3_prefix}index/{name}",
                Body=(root / name).read_bytes(),
                ServerSideEncryption="AES256",
            )
    print(
        json.dumps(
            {
                "runbooks": 10,
                "chunks": len(chunks),
                "new_live_embeddings": calls,
                "s3_snapshot": bool(settings.s3_bucket),
            }
        )
    )


if __name__ == "__main__":
    main()
