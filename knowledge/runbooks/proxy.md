# Reverse proxy gateway errors

ID: PROXY
Scope: Nginx reporting failed upstream connections or responses

## Symptoms
502 Bad Gateway; 504 Gateway Timeout; upstream prematurely closed connection.

These are project-authored investigation notes, not an official diagnosis. Use the supplied logs to establish observed symptoms and cite their original line identifiers. Treat configuration changes, impact and the exact root cause as unknown unless evidence supports them. This runbook suggests checks; CloudLens never executes changes to the affected system.

## Diagnostic checks
Compare proxy and application timestamps and request identifiers. Check the configured upstream host and port, process health and listening interface. Distinguish connection refusal, upstream closure and response timeout in proxy error logs. Inspect relevant connection and read timeout settings. A proxy 502 does not uniquely identify an application crash; incorrect upstream configuration can produce a similar symptom.

## Missing evidence
Collect surrounding application logs, relevant deployment configuration, dependency-side evidence and a known-good comparison. Preserve timestamps when present and label absent timestamps as unknown. Record evidence that contradicts a proposed cause as well as evidence supporting it. If only a generic failure message is available, report insufficient evidence and request context rather than asserting a cause.

## Recovery guidance
Correct the confirmed upstream address or application issue using the approved deployment process. Review timeout changes against measured behavior rather than simply increasing every limit. Validate proxy configuration before reloading. Verify the proxied endpoint, application health and an end-to-end request, and monitor for recurring gateway failures.

## Sources
- https://nginx.org/en/docs/http/ngx_http_proxy_module.html
