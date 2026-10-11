# Deployment

## Verified state

The owner created the direct-EC2 CloudFormation stack in Mumbai. Screenshots confirmed successful Docker builds, a healthy API container, a running web container on port 443 and a loaded HTTPS login page. Deployed model inference, private report upload, cookie behavior and container restart persistence have not yet been independently verified.

The CloudFront stack rolled back because AWS required account verification before creating distributions. This is an account-level restriction. The direct deployment avoids CloudFront and does not require a plan upgrade.

## Templates

| Template | Entry point | Use |
| --- | --- | --- |
| `infra/cloudlens-direct.json` | EC2 HTTPS, owner IPv4 /32 | Classroom fallback; self-signed certificate warning |
| `infra/cloudlens.json` | CloudFront HTTPS | Optional after account verification; generated origin secret |

Both define tagged project networking, one x86 `t3.small`, 12 GiB encrypted gp3 EBS, a private encrypted/versioned S3 bucket, an EC2 role, SSM management and a seven-day CloudWatch log group. Neither exposes SSH, the database or the API port. S3 report current/noncurrent versions expire after seven days. The bucket is retained when a stack is deleted and requires explicit project-only cleanup.

The direct template limits HTTPS443 to `DemoAccessCidr`, which must be the owner's current public IPv4 with `/32`. Update it if the presentation network changes. The CloudFront template permits origin HTTP80 only from the origin-facing prefix list and validates a generated secret header in Nginx. Browser-to-CloudFront is HTTPS; CloudFront-to-EC2 is HTTP, not end-to-end TLS.

The runtime role permits only the project S3 prefix, needed CloudWatch events and SSM management. The optional CloudFront variant also permits reading its generated origin secret. Gemini authentication uses a privately injected Google key, not an AWS role or browser credentials.

## Build and configure

Build frontend assets locally and ingest the real embeddings. `python3 infra/package.py` produces an allowlisted ZIP containing app code, lockfiles, built frontend and trusted index. It excludes local env files, databases, uploaded logs, vector caches and browser sessions.

Use [console steps](aws-console-steps.md) to create a change set, inspect project resources and transfer the ZIP through private S3. On EC2, `infra/install.sh --direct` verifies pinned Compose and Buildx release checksums, copies the index into the mounted data directory and launches the containers. `infra/configure.py --direct` uses hidden key/password prompts, generates a session secret and a seven-day self-signed TLS certificate, and writes mode-600 configuration. No secrets are in user-data, Git or image layers.

For CloudFront, use the installer without `--direct`. The script retrieves the generated header using the EC2 role. No local AWS credentials/profile should be copied to EC2.

The instance uses standard CPU credits to avoid surplus-credit charging. Benchmark memory/CPU credits under a real analysis before resizing. Frontend builds happen locally; no embedding model is loaded on EC2. SQLite and the index live outside container layers on EBS. Avoid stopping the instance during the demo: the public address/DNS can change, requiring a new allowed origin and certificate. Container restarts preserve its address.

## Acceptance checks

- HTTPS login and a synthetic real-model report with relevant retrieved guidance.
- Evidence selection, Markdown/JSON downloads and session-scoped history.
- Unauthorized/other-session denial and correct Origin/CSRF handling.
- Private redacted S3 report and sanitized CloudWatch event.
- History survives an API container restart; interrupted jobs become failed.
- Direct access is restricted to the intended IP or protected CloudFront origin.

Do not declare a complete deployment based solely on running containers. Use `docker compose -f infra/compose-direct.yaml ps` and bounded API logs for troubleshooting; never print private env files. For CloudFront use `infra/compose.yaml`.

## Costs and retention

Target gross demonstration consumption: at most $10, with a short 48-hour lifetime; this is a planning target, not a hard cap. Verified Mumbai planning rates were EC2 `t3.small` $0.0224/hour, gp3 $0.0912/GB-month and public IPv4 $0.005/hour. The assumed compute/storage/address subtotal is approximately $1.39 for 48 hours before taxes. Reserve additional allowance for S3, logs, optional CloudFront/Secrets Manager and external Gemini usage; verify current prices and account eligibility before launching elsewhere.

Google quota/pricing is separate from AWS credits. Model requests/retries are bounded by the persistent app budget. Budget alerts are delayed notifications, not hard spending limits. Schedule local `scripts.prune` for seven-day report retention; S3 and CloudWatch have lifecycle/retention rules. See [teardown](teardown.md) to stop ongoing project charges.
