# AWS console deployment

## Direct EC2 classroom deployment

1. Select Mumbai (`ap-south-1`) using an authorized provisioning identity. CloudFormation → Create stack → With new resources → Upload `infra/cloudlens-direct.json`.
2. Name the stack `cloudlens-demo`. Keep the Amazon Linux AMI parameter and `t3.small`. Set `DemoAccessCidr` to your public IPv4 plus `/32`. Add tag `Project=CloudLens`, acknowledge IAM resources, review the change set and create only these project resources.
3. Wait for `CREATE_COMPLETE`. Record `ApplicationURL`, `InstanceId` and `ArtifactBucket` privately. If creation fails, inspect the failed resource's Status reason before retrying.
4. In the output bucket, create `cloudlens/`, then `deploy/` inside it. Upload the generated `infra/private/cloudlens-deploy.zip`. Keep public access blocked.
5. EC2 → select the exact output InstanceId → Connect → SSM Session Manager → Connect. This is different from CloudShell. No SSH rule is required.
6. Replace YOUR_BUCKET below with ArtifactBucket and run commands one at a time:

```bash
sudo dnf install -y unzip
sudo aws s3 cp s3://YOUR_BUCKET/cloudlens/deploy/cloudlens-deploy.zip /tmp/cloudlens-deploy.zip --region ap-south-1
sudo unzip -o /tmp/cloudlens-deploy.zip -d /srv/cloudlens/source
cd /srv/cloudlens/source
sudo bash infra/install.sh --direct
```

Enter ArtifactBucket and ApplicationURL exactly from Outputs. Enter the Gemini key and a minimum-12-character demo password at hidden prompts. The installer generates the session secret and private self-signed certificate. Never put keys into shell commands, chat or screenshots. No AWS access keys/profile are needed on EC2.

Open ApplicationURL. A self-signed certificate warning is expected; acknowledge only for your own exact demo URL. It is not a publicly trusted certificate. Use synthetic data. Check login → sample → report → evidence → both downloads → history. Confirm private S3 artifacts and a sanitized CloudWatch event before calling the deployment complete.

```bash
cd /srv/cloudlens/source
sudo docker compose -f infra/compose-direct.yaml ps
sudo docker compose -f infra/compose-direct.yaml restart api
```

Reopen history after restart in the same browser session. If the network changes, update DemoAccessCidr to its public IPv4 /32. Avoid stopping the instance before the presentation because its hostname can change.

## Optional CloudFront deployment

An AWS account-verification restriction prevented the initial CloudFront distribution. Account and billing support can resolve verification; a paid support upgrade is not required merely to open that case. Do not repeatedly retry while the restriction remains.

After account verification, use `infra/cloudlens.json`, supply Mumbai's `com.amazonaws.global.cloudfront.origin-facing` prefix-list ID, and review a project-only change set. Secrets Manager generates the origin header. Its ARN, not its value, appears in Outputs. Use `infra/install.sh` without `--direct`; configuration additionally asks for OriginSecretArn. Browser access uses the default trusted CloudFront HTTPS hostname; origin transport remains HTTP with restricted ingress and the secret header.

Retained buckets from failed stacks require separate project-only cleanup. Do not delete other instances, buckets or roles. See [deployment](deployment.md) and [teardown](teardown.md).
