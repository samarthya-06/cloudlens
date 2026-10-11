# External API throttling

ID: THROTTLE
Scope: Dependencies limiting request rates or returning transient overload

## Symptoms
TooManyRequests; ThrottlingException; 429; rate limit exceeded.

These are project-authored investigation notes, not an official diagnosis. Use the supplied logs to establish observed symptoms and cite their original line identifiers. Treat configuration changes, impact and the exact root cause as unknown unless evidence supports them. This runbook suggests checks; CloudLens never executes changes to the affected system.

## Diagnostic checks
Identify the dependency, operation and throttling response. Inspect retry headers where provided, SDK retry configuration and total request attempts. Compare concurrency and request rates against documented limits. Separate throttling from authentication failures and persistent validation errors. Retrying all errors indiscriminately can amplify load. The supplied logs may show throttling without establishing how much traffic caused it.

## Missing evidence
Collect surrounding application logs, relevant deployment configuration, dependency-side evidence and a known-good comparison. Preserve timestamps when present and label absent timestamps as unknown. Record evidence that contradicts a proposed cause as well as evidence supporting it. If only a generic failure message is available, report insufficient evidence and request context rather than asserting a cause.

## Recovery guidance
Reduce verified concurrency or request frequency and use bounded retries with backoff and jitter. Cache suitable repeated work. Request quota changes only through the resource owner when justified. Verify that successful calls recover while total attempts remain bounded, and retain a clear failure message when the retry budget is exhausted.

## Sources
- https://docs.aws.amazon.com/sdkref/latest/guide/feature-retry-behavior.html
