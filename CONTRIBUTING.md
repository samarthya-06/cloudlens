# Contributing

Keep changes focused on evidence-grounded log analysis. Preserve the reviewed monochrome desktop design, explicit uncertainty, synthetic fixtures and source links. CloudLens does not apply repairs to incident targets.

Use Python 3.12 with the committed uv lockfile and the frontend npm lockfile. Run Ruff, backend tests, TypeScript checks and the frontend build before proposing changes. Separate deterministic mock tests from opt-in live AI evaluations, which consume quota.

Never commit runtime data or secrets. Use `.env.example` placeholders. Update deployment/evaluation documentation when behavior changes, and only describe outcomes as verified when evidence exists.

A pull request should explain the user-visible problem, resulting behavior and relevant validation. Do not add mobile layouts, new infrastructure services or automatic remediation without an agreed scope change.
