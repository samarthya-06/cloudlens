"""Run privately on EC2 through SSM; credentials never enter shell arguments."""

import getpass
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


def main():
    if os.geteuid() != 0:
        raise SystemExit("Run with sudo python3 infra/configure.py")
    bucket = input("ArtifactBucket output: ").strip()
    origin = input("ApplicationURL output (https://...): ").strip().rstrip("/")
    direct = "--direct" in sys.argv
    secret_arn = "" if direct else input("OriginSecretArn output: ").strip()
    key = getpass.getpass("Gemini API key (hidden): ").strip()
    password = getpass.getpass("Demo password (hidden; minimum 12 characters): ")
    if (
        not bucket
        or not origin.startswith("https://")
        or (not direct and not secret_arn.startswith("arn:"))
    ):
        raise SystemExit("Invalid stack outputs; no configuration written.")
    if not key or len(password) < 12 or any(c in key + password for c in "\n\r"):
        raise SystemExit("Invalid key/password; no configuration written.")
    if direct:
        host = urlparse(origin).hostname or ""
        if not host.endswith(".amazonaws.com") or "/" in host:
            raise SystemExit("Use the EC2 ApplicationURL output exactly.")
        tls = Path("/srv/cloudlens/tls")
        tls.mkdir(mode=0o700, exist_ok=True)
        os.umask(0o077)
        subprocess.run(
            [
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-days",
                "7",
                "-keyout",
                str(tls / "server.key"),
                "-out",
                str(tls / "server.crt"),
                "-subj",
                f"/CN={host}",
                "-addext",
                f"subjectAltName=DNS:{host}",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        os.chmod(tls / "server.key", 0o600)
        header = ""
    else:
        result = subprocess.run(
            [
                "aws",
                "secretsmanager",
                "get-secret-value",
                "--region",
                "ap-south-1",
                "--secret-id",
                secret_arn,
                "--query",
                "SecretString",
                "--output",
                "text",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        header = json.loads(result.stdout)["header"]
    values = {
        "AWS_REGION": "ap-south-1",
        "AI_PROVIDER": "gemini",
        "GEMINI_API_KEY": key,
        "GEMINI_MODEL_ID": "gemini-3.5-flash-lite",
        "EMBEDDING_MODEL_ID": "gemini-embedding-001",
        "EMBEDDING_DIMENSIONS": "768",
        "S3_BUCKET": bucket,
        "S3_PREFIX": "cloudlens/",
        "ALLOWED_ORIGINS": origin,
        "DEMO_PASSWORD": password,
        "SESSION_SECRET": secrets.token_urlsafe(48),
        "COOKIE_SECURE": "true",
        "DATABASE_PATH": "/data/cloudlens.sqlite",
        "INDEX_PATH": "/data/index",
        "ARTIFACT_PATH": "/data/artifacts",
        "MAX_MODEL_CALLS": "120",
        "MODEL_TIMEOUT_SECONDS": "60",
        "INVESTIGATION_TIMEOUT_SECONDS": "180",
    }
    target = Path(__file__).resolve().parent / "private"
    target.mkdir(mode=0o700, exist_ok=True)
    os.chmod(target, 0o700)
    # Compose env_file raw preserves dollar signs and quote characters in secrets.
    os.umask(0o077)
    files = {
        "runtime.env": "".join(f"{k}={v}\n" for k, v in values.items()),
        "origin.env": f"ORIGIN_SECRET={header}\n",
    }
    if direct:
        files.pop("origin.env")
    for name, contents in files.items():
        path = target / name
        path.write_text(contents)
        os.chmod(path, 0o600)
    print("Private configuration written. No secrets printed.")


if __name__ == "__main__":
    main()
