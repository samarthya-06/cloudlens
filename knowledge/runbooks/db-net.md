# Database reachability failures

ID: DB-NET
Scope: Database connections refused, unreachable or timing out

## Symptoms
connection refused; connection timed out; could not translate host name.

These are project-authored investigation notes, not an official diagnosis. Use the supplied logs to establish observed symptoms and cite their original line identifiers. Treat configuration changes, impact and the exact root cause as unknown unless evidence supports them. This runbook suggests checks; CloudLens never executes changes to the affected system.

## Diagnostic checks
Distinguish DNS failure, connection refusal, network timeout and database authentication rejection. Confirm the intended endpoint and port from configuration without showing credentials. Test DNS and TCP reachability from the same network as the application. Inspect database availability, routing, security groups and network ACLs with the resource owner. Compare timestamps with maintenance events. A refused connection and a timed-out connection suggest different checks; neither proves a security group fault.

## Missing evidence
Collect surrounding application logs, relevant deployment configuration, dependency-side evidence and a known-good comparison. Preserve timestamps when present and label absent timestamps as unknown. Record evidence that contradicts a proposed cause as well as evidence supporting it. If only a generic failure message is available, report insufficient evidence and request context rather than asserting a cause.

## Recovery guidance
Restore only the verified endpoint, listener or network configuration using the approved change process. Avoid broad public ingress rules as a shortcut. Verify DNS resolution, an application-side TCP connection and a database query. Record which controlled change improved reachability and keep a rollback plan.

## Sources
- https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Troubleshooting.html
