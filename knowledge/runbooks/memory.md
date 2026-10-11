# Memory exhaustion

ID: MEMORY
Scope: Processes terminated or allocation failing under memory limits

## Symptoms
OOMKilled; out of memory; MemoryError; allocation failed.

These are project-authored investigation notes, not an official diagnosis. Use the supplied logs to establish observed symptoms and cite their original line identifiers. Treat configuration changes, impact and the exact root cause as unknown unless evidence supports them. This runbook suggests checks; CloudLens never executes changes to the affected system.

## Diagnostic checks
Correlate application errors with container exit state, kernel messages and memory usage near the event. Inspect configured container and host limits. Distinguish an application allocation failure from a kernel OOM termination. Compare workload and memory trends; a single termination does not establish a memory leak. Check whether another process consumed host capacity. Gather a safe diagnostic profile without retaining customer data or secrets.

## Missing evidence
Collect surrounding application logs, relevant deployment configuration, dependency-side evidence and a known-good comparison. Preserve timestamps when present and label absent timestamps as unknown. Record evidence that contradicts a proposed cause as well as evidence supporting it. If only a generic failure message is available, report insufficient evidence and request context rather than asserting a cause.

## Recovery guidance
Reduce verified workload pressure or adjust an approved resource limit within available host capacity. Investigate retained allocations before asserting a leak. Any restart requires the operator’s approval and may only restore service temporarily. Verify stable memory usage, no additional OOM events and normal request behavior during a representative run.

## Sources
- https://docs.docker.com/engine/containers/resource_constraints/
