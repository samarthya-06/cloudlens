import re
from collections import Counter
from datetime import datetime

from app.schemas import Evidence, LogLine

REDACTIONS = [
    (
        re.compile(
            r"(?i)(\b(?:password|passwd|pwd|token|secret|api[_-]?key|access[_-]?key)\b\s*[=:]\s*)(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)"
        ),
        r"\1[REDACTED]",
    ),
    (re.compile(r"(?i)(\b[a-z][a-z0-9+.-]*://[^\s/:@]+:)[^\s@]+(@)"), r"\1[REDACTED]\2"),
    (re.compile(r"(?i)(\bauthorization\s*[:=]\s*(?:bearer|basic)\s+)[^\s]+"), r"\1[REDACTED]"),
    (re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"), "[REDACTED]"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"), "[REDACTED]"),
]
STAMP = re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?")
LEVEL = re.compile(r"\b(TRACE|DEBUG|INFO|WARN(?:ING)?|ERROR|FATAL|CRITICAL)\b", re.I)
SIGNAL = re.compile(r"error|exception|failed|denied|timeout|timed out|out of memory|no space", re.I)


def decode_input(data: bytes, maximum: int) -> str:
    if len(data) > maximum:
        raise ValueError("This input exceeds 256 KiB. Choose a smaller log excerpt.")
    if not data or not data.strip():
        raise ValueError("Provide non-empty application logs.")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Upload a UTF-8 .txt or .log file.") from exc
    if any(ord(c) < 32 and c not in "\n\r\t" for c in text):
        raise ValueError("Binary input is not supported.")
    return text


def redact(text: str) -> tuple[str, int]:
    count = 0
    for pattern, replacement in REDACTIONS:
        text, n = pattern.subn(replacement, text)
        count += n
    return text, count


def parse_logs(text: str) -> Evidence:
    text, redactions = redact(text)
    lines: list[LogLine] = []
    signals: list[int] = []
    group = 0
    for number, raw in enumerate(text.splitlines(), 1):
        match, severity = STAMP.search(raw), LEVEL.search(raw)
        timestamp = None
        if match:
            try:
                datetime.fromisoformat(match[0].replace("Z", "+00:00"))
                timestamp = match[0]
            except ValueError:
                pass
        if (
            timestamp
            or severity
            or not lines
            or (not raw.startswith((" ", "\t")) and not raw.startswith("Traceback"))
        ):
            group += 1
        level = severity[1].upper() if severity else "UNKNOWN"
        if level == "WARNING":
            level = "WARN"
        lines.append(
            LogLine(
                id=f"L{number:04d}",
                number=number,
                text=raw,
                timestamp=timestamp,
                severity=level,
                group=group,
            )
        )
        if level in {"WARN", "ERROR", "FATAL", "CRITICAL"} or SIGNAL.search(raw):
            signals.append(number - 1)
    groups: dict[int, list[int]] = {}
    for i, line in enumerate(lines):
        groups.setdefault(line.group, []).append(i)
    selected: set[int] = set()
    for index in signals:
        selected.update(range(max(0, index - 3), min(len(lines), index + 4)))
        selected.update(groups[lines[index].group])
    if not selected:
        selected.update(range(min(100, len(lines))))
    chosen: list[LogLine] = []
    chars = 0
    for index in sorted(selected):
        line = lines[index]
        # Never truncate the text of an individual line or renumber sources.
        if len(chosen) >= 100 or chars + len(line.text) > 20000:
            continue
        chosen.append(line)
        chars += len(line.text)
    signatures = [re.sub(r"\b\d+\b", "#", STAMP.sub("", lines[i].text)).strip() for i in signals]
    counts = Counter(signatures)
    query = "\n".join(dict.fromkeys(signatures))[:6000]
    if not query:
        query = "\n".join(line.text for line in chosen)[:6000]
    return Evidence(
        lines=chosen,
        total_lines=len(lines),
        omitted_lines=len(lines) - len(chosen),
        redactions=redactions,
        repeated_errors={k: v for k, v in counts.items() if v > 1},
        query=query or "No usable log evidence",
    )
