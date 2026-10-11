# CloudLens teardown

The direct EC2 classroom stack exists. Record its exact stack/resource IDs privately. Never delete resources by a generic name alone.

1. Confirm required reports and deployment evidence are backed up. Keep only redacted synthetic artifacts.
2. If using CloudFront, disable the exact CloudLens CloudFront distribution and wait until the update is deployed. Then delete it or let the CloudLens stack handle its lifecycle. Do not terminate the origin before deciding whether the demo is finished.
3. Delete the exact CloudLens application stack. Inspect the change set/resource list and `Project=CloudLens` tags. Instance termination also deletes its root EBS volume and local SQLite history; preserve required data first.
4. The S3 bucket is deliberately retained by CloudFormation. Delete only its CloudLens objects after confirming backup needs, then remove that exact retained bucket. Never use a broad bucket wipe against an unverified name.
5. Confirm project security groups, VPC routes, role/profile and log group are gone or intentionally retained. Check Billing for residual EC2, IPv4, EBS, S3 and CloudFront consumption.
6. If an earlier project-only local-access stack remains, review and remove it only when no longer needed. IAM users are separate; remove them only with explicit authorization. Logout the project CLI session when finished.

CloudFront deletion requires disabling and waiting; retained buckets require separate handling. These operations have not been rehearsed or executed.
