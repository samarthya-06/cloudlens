# Presentation outline

1. Problem and workflow: logs → evidence → retrieved guidance → incident report.
2. Desktop demo: protected access, upload/paste and three synthetic incidents.
3. Deterministic preparation: validation, redaction, line IDs, multiline context and missing timestamps.
4. Real RAG: original runbooks, Gemini vectors, NumPy cosine similarity, source metadata. Similarity is not a probability.
5. Generation and grounding: Gemini, structured schema, citation validation, facts versus hypotheses, bounded repair.
6. AWS architecture: EC2, EBS/SQLite, private S3, runtime role, CloudFront and CloudWatch. Describe only services actually deployed.
7. Evaluation: actual hit@3, live outcomes, synthetic fixtures and meaningful tests. Clearly distinguish mocked checks from live results.
8. Limitations, cost target and project teardown. No automatic incident repairs or production-readiness claim.

No slide deck has been created. Fill measured results after live verification.

Current implementation uses Gemini Developer API generation (`gemini-3.5-flash-lite`) and embeddings (`gemini-embedding-001`, normalized 768 dimensions). AWS hosts the planned application infrastructure; AI processing is external to AWS. Bedrock is no longer part of the application runtime. Live synthetic reports and retrieval results are saved in docs/evidence/runtime.
