# Three-minute presentation demo

Use only synthetic logs. Do not describe fixtures as live inference.

**0:00–0:30:** Explain the problem: a log excerpt shows symptoms, but useful investigation needs surrounding evidence and relevant troubleshooting guidance. Enter the protected demo workspace.

**0:30–1:30:** Load Database authentication. Point out the synthetic label and input limit. Select Analyse logs. Explain that Python redacts secrets and selects numbered evidence, Gemini embeds the error query, and NumPy retrieves matching project runbooks before Gemini generates a report. Only demonstrate live processing after its probes pass.

**1:30–2:15:** Read an observed fact, then a possible cause. Explain why a credential mismatch is a hypothesis. Select an evidence chip to highlight the actual line; select a runbook chip to show its guidance and original documentation link. Explain the missing evidence and proposed checks. CloudLens does not perform repairs.

**2:15–2:40:** Download Markdown or JSON. Open History and reopen the report. Mention that this demo uses SQLite on EBS and private S3 artifacts in deployment.

**2:40–3:00:** Explain limitations: best-effort redaction, incomplete logs, AI-assisted hypotheses requiring verification, single-instance queue, no calibrated confidence percentages. Show ambiguous input if time allows.

Rehearse S3 AccessDenied and upstream timeouts as alternative examples. Several S3 policies can cause denial; timeout logs do not prove CPU overload. A previously generated backup report must be labelled as such. Rehearsal and live deployment are still pending.

Current implementation uses Gemini Developer API generation (`gemini-3.5-flash-lite`) and embeddings (`gemini-embedding-001`, normalized 768 dimensions). AWS hosts the planned application infrastructure; AI processing is external to AWS. Bedrock is no longer part of the application runtime. Live synthetic reports and retrieval results are saved in docs/evidence/runtime.
