# S3 access denial

ID: S3-DENY
Scope: S3 API requests returning AccessDenied

## Symptoms
AccessDenied; PutObject denied; S3 403 Forbidden.

These are project-authored investigation notes, not an official diagnosis. Use the supplied logs to establish observed symptoms and cite their original line identifiers. Treat configuration changes, impact and the exact root cause as unknown unless evidence supports them. This runbook suggests checks; CloudLens never executes changes to the affected system.

## Diagnostic checks
Confirm the operation, bucket, object prefix and actual calling IAM role. Inspect relevant identity policy, bucket policy, organization controls and permission boundaries. An explicit deny can override an allow. Check encryption requirements and KMS permissions when encryption uses a customer-managed key. Review object ownership and endpoint policy where applicable. The error alone does not identify which policy denied the request. Do not infer that adding s3:* is necessary.

## Missing evidence
Collect surrounding application logs, relevant deployment configuration, dependency-side evidence and a known-good comparison. Preserve timestamps when present and label absent timestamps as unknown. Record evidence that contradicts a proposed cause as well as evidence supporting it. If only a generic failure message is available, report insufficient evidence and request context rather than asserting a cause.

## Recovery guidance
Have the resource owner correct only the confirmed policy or encryption discrepancy with least privilege. Do not make the bucket public or remove unrelated denies. Verify the same operation against an authorized test key under the intended role and confirm that unauthorized access remains denied. Preserve a local redacted artifact if an upload fails.

## Sources
- https://docs.aws.amazon.com/AmazonS3/latest/userguide/troubleshoot-403-errors.html
