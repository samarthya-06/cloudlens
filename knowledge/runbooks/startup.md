# Application startup and migration failures

ID: STARTUP
Scope: Services failing during initialization or schema migrations

## Symptoms
migration failed; startup failed; schema version mismatch; revision not found.

These are project-authored investigation notes, not an official diagnosis. Use the supplied logs to establish observed symptoms and cite their original line identifiers. Treat configuration changes, impact and the exact root cause as unknown unless evidence supports them. This runbook suggests checks; CloudLens never executes changes to the affected system.

## Diagnostic checks
Identify the first failing startup or migration step and preserve its trace. Compare deployed application version, migration files and current database revision. Confirm database reachability and access before investigating schema changes. Inspect whether another migration is active. A failed migration does not establish that a database rollback is safe. Collect the exact revision and failure details without exposing connection credentials.

## Missing evidence
Collect surrounding application logs, relevant deployment configuration, dependency-side evidence and a known-good comparison. Preserve timestamps when present and label absent timestamps as unknown. Record evidence that contradicts a proposed cause as well as evidence supporting it. If only a generic failure message is available, report insufficient evidence and request context rather than asserting a cause.

## Recovery guidance
Apply only an approved migration or rollback after checking backups, compatibility and whether the failed step partially changed data. Do not automatically downgrade a database from a generic startup error. Verify the expected schema revision, successful startup and representative read/write behavior under the application’s intended permissions.

## Sources
- https://alembic.sqlalchemy.org/en/latest/tutorial.html
