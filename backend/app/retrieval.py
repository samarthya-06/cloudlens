import hashlib
import json
import re
from pathlib import Path

import numpy as np

from app.config import Settings
from app.schemas import Chunk

INDEX_VERSION = "cloudlens-headings-v1"


def chunk_runbooks(root: Path) -> list[Chunk]:
    chunks = []
    for path in sorted(root.glob("*.md")):
        text = path.read_text()
        rid = re.search(r"^ID: (.+)$", text, re.M)[1]
        title = text.splitlines()[0].removeprefix("# ")
        urls = re.findall(r"https://[^\s)]+", text)
        sections = [
            section
            for section in re.split(r"^## ", text, flags=re.M)[1:]
            if not section.startswith("Sources\n")
        ]
        # These short original runbooks fit a single roughly 300–500-token chunk.
        # Retain all headings and their scope rather than embedding tiny isolated bullets.
        body = "\n## ".join(sections)
        content = f"{title}\nScope: {re.search(r'^Scope: (.+)$', text, re.M)[1]}\n## {body}"
        chunks.append(
            Chunk(
                id=f"{rid}:investigation:1",
                runbook_id=rid,
                title=title,
                section="Diagnostic checks and recovery",
                text=content,
                source_urls=urls,
                content_hash=hashlib.sha256(content.encode()).hexdigest(),
            )
        )
    return chunks


class VectorIndex:
    def __init__(self, settings: Settings):
        self.settings = settings

    def load(self):
        path = self.settings.index_path
        if not (path / "metadata.json").exists():
            raise RuntimeError(
                "The real embedding index is not built yet. Run ingestion after AWS access is verified."
            )
        metadata = json.loads((path / "metadata.json").read_text())
        expected = {
            "model": self.settings.embedding_model_id,
            "dimensions": self.settings.embedding_dimensions,
            "normalize": True,
            "version": INDEX_VERSION,
            "region": self.settings.inference_location,
        }
        if any(metadata.get(k) != value for k, value in expected.items()):
            raise RuntimeError(
                "Index configuration differs from the query embedding configuration. Rebuild it."
            )
        chunks = [Chunk.model_validate(c) for c in json.loads((path / "chunks.json").read_text())]
        with np.load(path / "index.npz", allow_pickle=False) as data:
            matrix = data["vectors"].copy()
        if not chunks or len({c.id for c in chunks}) != len(chunks):
            raise ValueError("Index chunks are empty or duplicated")
        if (
            matrix.shape != (len(chunks), self.settings.embedding_dimensions)
            or not np.isfinite(matrix).all()
        ):
            raise ValueError("Index matrix is invalid")
        if not np.allclose(np.linalg.norm(matrix, axis=1), 1, atol=1e-4):
            raise ValueError("Index vectors must be normalized")
        if (
            hashlib.sha256((path / "chunks.json").read_bytes()).hexdigest()
            != metadata["chunks_sha256"]
        ):
            raise ValueError("Index chunk metadata does not match snapshot")
        return matrix, chunks, metadata

    def retrieve(self, query_vector: np.ndarray, count: int = 5):
        matrix, chunks, metadata = self.load()
        norms = np.linalg.norm(matrix, axis=1)
        scores = matrix @ query_vector / (norms * np.linalg.norm(query_vector))
        order = np.argsort(-scores)[:count]
        return [
            chunks[int(i)].model_copy(update={"similarity": float(scores[i])}) for i in order
        ], metadata
