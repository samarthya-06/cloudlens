"""Create local secrets without printing them or replacing existing configuration."""

import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[2]
target = root / ".env"
if target.exists():
    raise SystemExit(".env already exists; update it locally without sharing its contents.")
text = (root / ".env.example").read_text()
text = text.replace("DEMO_PASSWORD=\n", f"DEMO_PASSWORD={secrets.token_urlsafe(12)}\n")
text = text.replace("SESSION_SECRET=\n", f"SESSION_SECRET={secrets.token_urlsafe(48)}\n")
target.write_text(text)
target.chmod(0o600)
print(
    "Created private .env. Open it locally to read the demo password and configure GEMINI_API_KEY."
)
