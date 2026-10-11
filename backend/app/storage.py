import json

import boto3
from botocore.config import Config


class ArtifactStore:
    def __init__(self, settings):
        self.settings = settings

    def save(self, identifier: str, payload: dict):
        # identifiers are generated server-side, never uploaded filenames.
        data = json.dumps(payload, ensure_ascii=False).encode()
        if self.settings.s3_bucket:
            client = boto3.Session(profile_name=self.settings.aws_profile).client(
                "s3",
                region_name=self.settings.aws_region,
                config=Config(
                    connect_timeout=5, read_timeout=15, retries={"total_max_attempts": 2}
                ),
            )
            key = f"{self.settings.s3_prefix}reports/{identifier}.json"
            client.put_object(
                Bucket=self.settings.s3_bucket,
                Key=key,
                Body=data,
                ContentType="application/json",
                ServerSideEncryption="AES256",
            )
            return {"mode": "s3", "key": key}
        path = self.settings.artifact_path
        path.mkdir(parents=True, exist_ok=True)
        (path / f"{identifier}.json").write_bytes(data)
        return {"mode": "local"}


def markdown_report(incident: dict) -> str:
    report = incident["report"]
    out = [
        f"# {report['title']}",
        report["summary"],
        f"Status: {report['analysis_status']}",
        "AI-assisted hypotheses require verification. CloudLens does not execute repairs.",
    ]
    for key in [
        "observed_facts",
        "timeline",
        "hypotheses",
        "recommended_checks",
        "recovery_guidance",
    ]:
        out.append("## " + key.replace("_", " ").title())
        for item in report[key]:
            out.append(
                "- "
                + " | ".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in item.items())
            )
    out += ["## Limitations", *["- " + value for value in report["limitations"]], "## Log evidence"]
    for line in incident["evidence"]["lines"]:
        out.append(f"    {line['id']}: {line['text']}")
    out.append("## Retrieved sources")
    for chunk in incident["retrieved_chunks"]:
        out += [
            f"### {chunk['id']} — {chunk['title']} / {chunk['section']}",
            chunk["text"],
            *chunk["source_urls"],
        ]
    return "\n\n".join(out) + "\n"
