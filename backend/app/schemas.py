from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class References(StrictModel):
    log_refs: list[str] = Field(default_factory=list, max_length=100)
    runbook_refs: list[str] = Field(default_factory=list, max_length=10)


class Fact(References):
    statement: str = Field(min_length=1, max_length=2000)
    log_refs: list[str] = Field(min_length=1, max_length=100)


class Event(References):
    timestamp: str | None
    event: str = Field(min_length=1, max_length=2000)
    log_refs: list[str] = Field(min_length=1, max_length=100)


class Hypothesis(References):
    possible_cause: str
    rank: Literal["leading", "alternative"]
    evidence_against: str | None
    missing_evidence: list[str] = Field(min_length=1, max_length=10)
    log_refs: list[str] = Field(min_length=1, max_length=100)
    runbook_refs: list[str] = Field(min_length=1, max_length=10)


class Check(References):
    action: str
    why: str
    expected_observation: str


class Recovery(References):
    proposed_action: str
    prerequisites: list[str]
    verification_steps: list[str]
    runbook_refs: list[str] = Field(min_length=1, max_length=10)


class ModelReport(StrictModel):
    title: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=1, max_length=4000)
    analysis_status: Literal["incident_detected", "no_incident_detected", "insufficient_evidence"]
    observed_facts: list[Fact] = Field(max_length=20)
    timeline: list[Event] = Field(max_length=20)
    hypotheses: list[Hypothesis] = Field(max_length=8)
    recommended_checks: list[Check] = Field(max_length=12)
    recovery_guidance: list[Recovery] = Field(max_length=8)
    limitations: list[str] = Field(min_length=1, max_length=15)

    @model_validator(mode="after")
    def require_grounding(self):
        if self.analysis_status == "incident_detected" and not self.observed_facts:
            raise ValueError("An incident requires observed log facts")
        if self.analysis_status != "incident_detected" and self.recovery_guidance:
            raise ValueError("Recovery guidance requires a supported incident")
        return self


class LogLine(StrictModel):
    id: str
    number: int
    text: str
    timestamp: str | None
    severity: str
    group: int


class Evidence(StrictModel):
    lines: list[LogLine]
    total_lines: int
    omitted_lines: int
    redactions: int
    repeated_errors: dict[str, int]
    query: str


class Chunk(StrictModel):
    id: str
    runbook_id: str
    title: str
    section: str
    text: str
    source_urls: list[str]
    content_hash: str
    similarity: float | None = None


def validate_references(report: ModelReport, evidence: Evidence, chunks: list[Chunk]) -> None:
    logs = {line.id: line for line in evidence.lines}
    runbooks = {chunk.id for chunk in chunks}
    for section in [
        report.observed_facts,
        report.timeline,
        report.hypotheses,
        report.recommended_checks,
        report.recovery_guidance,
    ]:
        for item in section:
            if not item.log_refs and not item.runbook_refs:
                raise ValueError("Every claim/check needs supplied references")
            if set(item.log_refs) - logs.keys() or set(item.runbook_refs) - runbooks:
                raise ValueError("Unknown evidence reference")
    for event in report.timeline:
        known = {logs[ref].timestamp for ref in event.log_refs if logs[ref].timestamp}
        if event.timestamp is not None and event.timestamp not in known:
            raise ValueError("Timeline timestamp must exist on its referenced lines")
