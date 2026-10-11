"""Package the built app and trusted index; explicitly exclude private/runtime data."""

import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
files = []
for directory in ("backend/app", "backend/scripts", "frontend/dist"):
    files.extend(
        p
        for p in (root / directory).rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    )
for name in (
    "backend/pyproject.toml",
    "backend/uv.lock",
    ".dockerignore",
    "infra/backend.Dockerfile",
    "infra/frontend.Dockerfile",
    "infra/compose.yaml",
    "infra/nginx.conf.template",
    "infra/configure.py",
    "infra/frontend-direct.Dockerfile",
    "infra/nginx.direct.conf",
    "infra/compose-direct.yaml",
    "infra/install.sh",
):
    files.append(root / name)
for name in ("index.npz", "chunks.json", "metadata.json"):
    path = root / "runtime/index" / name
    if path.exists():
        files.append(path)
if not (root / "runtime/index/index.npz").exists():
    raise SystemExit("Real embedding index missing; run ingestion first.")
if not (root / "frontend/dist/index.html").exists():
    raise SystemExit("Frontend build missing; run npm run build first.")
target = root / "infra/private/cloudlens-deploy.zip"
target.parent.mkdir(exist_ok=True)
with ZipFile(target, "w", ZIP_DEFLATED) as archive:
    for path in sorted(files):
        archive.write(path, path.relative_to(root))
target.chmod(0o600)
print(f"Created {target}: {len(files)} files, {target.stat().st_size} bytes")
print("SHA256:", hashlib.sha256(target.read_bytes()).hexdigest())
