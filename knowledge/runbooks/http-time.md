# Upstream request timeouts

ID: HTTP-TIME
Scope: Application HTTP clients exceeding configured deadlines

## Symptoms
ReadTimeout; ConnectTimeout; upstream request timed out; 504.

These are project-authored investigation notes, not an official diagnosis. Use the supplied logs to establish observed symptoms and cite their original line identifiers. Treat configuration changes, impact and the exact root cause as unknown unless evidence supports them. This runbook suggests checks; CloudLens never executes changes to the affected system.

## Diagnostic checks
Identify whether the timeout occurred while connecting, reading, writing or waiting for a connection pool slot. Compare client and upstream request IDs, timestamps and configured timeouts. Inspect upstream latency, availability and dependency metrics. Check network reachability for connection timeouts and response behavior for read timeouts. Repeated timeouts alone do not establish CPU overload, traffic volume or memory pressure. Collect metrics before ranking those explanations.

## Missing evidence
Collect surrounding application logs, relevant deployment configuration, dependency-side evidence and a known-good comparison. Preserve timestamps when present and label absent timestamps as unknown. Record evidence that contradicts a proposed cause as well as evidence supporting it. If only a generic failure message is available, report insufficient evidence and request context rather than asserting a cause.

## Recovery guidance
Address a verified upstream or connectivity issue through its owner. Adjust deadlines only after measuring normal latency and reviewing user impact. Bound retries and use backoff for transient failures; avoid multiplying load with unlimited retry loops. Verify successful requests, acceptable latency and fewer timeout errors under a representative workload.

## Sources
- https://www.python-httpx.org/advanced/timeouts/
