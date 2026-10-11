# Evaluation

## Deterministic verification

26 backend tests passed: parsing, multiline grouping, stable line IDs, bounded evidence, redaction, invalid uploads, schema/reference/timestamp validation, bounded repair, healthy/insufficient-evidence contracts, Gemini retry classification, persistent model budget, Origin/CSRF checks, session ownership, queue limits, timeout/late-result behavior and restart recovery. Provider transport is mocked for repeatability; these tests do not prove live inference.

Ruff and frontend TypeScript/build checks passed. Desktop browser checks cover keyboard focus, upload/paste behavior, failure states and report source highlighting. A missing-index scenario is skipped when the local real index exists. Fixture rendering is labelled; it is not live generation evidence. Mobile is outside the implemented scope.

## Live retrieval and generation

Ten original runbooks were embedded with `gemini-embedding-001`: normalized 768-dimensional document and query vectors with matching configuration. Twelve fixed labelled queries achieved **12/12 hit@3**; see [retrieval results](evidence/runtime/retrieval.json). Expected labels were not changed to conceal misses.

Six synthetic live generation fixtures passed schema, citation-ID and expected-status checks: database authentication, S3 denial, upstream timeout, healthy logs, ambiguous evidence and prompt injection. [Generation review](evidence/runtime/generation.json) records qualitative semantic checks and limitations. [Stored reports](evidence/runtime/live-reports/) are previously generated outputs, not a promise of new live calls.

Review preserved credential/policy uncertainty, missing metrics, unknown timestamps, healthy-log limitations and untrusted embedded instructions. Valid reference IDs alone cannot establish that an assertion is supported. Six synthetic examples are not a general accuracy guarantee.

The real local browser journey generated a report, selected evidence, downloaded redacted Markdown and reopened persisted history. A separate API restart check reopened history and JSON download with the existing session. The [live desktop preview](evidence/runtime/desktop-report-live.png) uses synthetic logs.

## AWS verification

Owner screenshots confirmed the direct-EC2 stack CREATE_COMPLETE, container images built, API healthy, web listening on443 and HTTPS login page loading. The certificate is self-signed and access is limited to the owner IP. Deployed model generation, report upload privacy, sanitized CloudWatch events, cross-session behavior and container restart persistence still require explicit checks. Local tests are not substituted for those deployment checks.

CloudFront creation was blocked by AWS account verification. The direct deployment avoids that dependency. It does not provide a publicly trusted certificate.
