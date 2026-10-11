# Security

Never commit `.env`, API keys, demo passwords, session secrets, AWS credentials, private TLS keys, uploaded logs, databases or browser session files. Placeholder examples are safe to publish; live configuration is not.

Use synthetic logs for demonstrations. Redaction catches common patterns but cannot guarantee that arbitrary input contains no sensitive data. AI requests use Google Gemini outside AWS. Never render generated HTML or execute generated commands.

Deploy with a narrow EC2 role, private S3, restricted ingress and HTTPS. The classroom fallback uses a self-signed certificate and owner-IP access; it is not a publicly trusted HTTPS service. Do not use it for sensitive data.

Report suspected vulnerabilities through GitHub private vulnerability reporting when enabled. If unavailable, contact the maintainer privately before disclosing exploit details. Do not include credentials or real uploaded logs in public issues. Rotate exposed keys at their provider immediately; deleting a file does not remove it from Git history.
