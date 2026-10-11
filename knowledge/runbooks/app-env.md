# Missing environment variables

ID: APP-ENV
Scope: Application configuration absent at runtime

## Symptoms
KeyError environment; missing required configuration; environment variable not set.

These are project-authored investigation notes, not an official diagnosis. Use the supplied logs to establish observed symptoms and cite their original line identifiers. Treat configuration changes, impact and the exact root cause as unknown unless evidence supports them. This runbook suggests checks; CloudLens never executes changes to the affected system.

## Diagnostic checks
Identify the missing variable name and which process requires it. Compare the service environment with the expected deployment configuration; a terminal environment may differ from the container environment. Check spelling, case and whether configuration was injected before process startup. Inspect the startup validation path. Redact secret values when collecting evidence. Missing configuration may prevent startup, but it does not prove that every request failed.

## Missing evidence
Collect surrounding application logs, relevant deployment configuration, dependency-side evidence and a known-good comparison. Preserve timestamps when present and label absent timestamps as unknown. Record evidence that contradicts a proposed cause as well as evidence supporting it. If only a generic failure message is available, report insufficient evidence and request context rather than asserting a cause.

## Recovery guidance
Supply the verified missing setting through the approved configuration mechanism. Keep credentials outside source control and images. Restart only under the operator’s approved process if the application reads settings at startup. Verify configuration validation, readiness and a representative request without printing sensitive values.

## Sources
- https://docs.python.org/3/library/os.html#os.environ
