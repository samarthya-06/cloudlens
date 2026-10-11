# Database authentication failures

ID: DB-AUTH
Scope: PostgreSQL application login rejected

## Symptoms
password authentication failed; authentication failed for user; role login rejected.

These are project-authored investigation notes, not an official diagnosis. Use the supplied logs to establish observed symptoms and cite their original line identifiers. Treat configuration changes, impact and the exact root cause as unknown unless evidence supports them. This runbook suggests checks; CloudLens never executes changes to the affected system.

## Diagnostic checks
Compare the deployed database username, host, database and credential source against the approved configuration. Inspect secret version identifiers without displaying secret values. Ask the database owner for the server-side authentication rejection and the applicable host authentication rule. Check whether the role can log in and whether a recent deployment changed its environment. A password authentication error does not establish which configuration value is wrong.

## Missing evidence
Collect surrounding application logs, relevant deployment configuration, dependency-side evidence and a known-good comparison. Preserve timestamps when present and label absent timestamps as unknown. Record evidence that contradicts a proposed cause as well as evidence supporting it. If only a generic failure message is available, report insufficient evidence and request context rather than asserting a cause.

## Recovery guidance
Correct a confirmed configuration discrepancy through the approved secret or deployment process. Do not reset passwords merely because a client login failed. If an authentication policy is the cause, obtain approval before changing it. Verify a fresh connection from the application environment, a successful health check and absence of repeated authentication failures.

## Sources
- https://www.postgresql.org/docs/current/client-authentication.html
