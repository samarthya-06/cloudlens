# Disk capacity exhaustion

ID: DISK
Scope: Writes failing because a filesystem or inode pool is full

## Symptoms
No space left on device; ENOSPC; disk full; inode exhaustion.

These are project-authored investigation notes, not an official diagnosis. Use the supplied logs to establish observed symptoms and cite their original line identifiers. Treat configuration changes, impact and the exact root cause as unknown unless evidence supports them. This runbook suggests checks; CloudLens never executes changes to the affected system.

## Diagnostic checks
Identify the path and mounted filesystem used by the failed write. Check both byte capacity and inode availability; free bytes do not rule out inode exhaustion. Inspect log growth, temporary files and retention settings without deleting evidence. If a volume was expanded, verify whether its partition and filesystem were extended as required. A disk error does not prove that increasing the cloud volume alone will fix the application.

## Missing evidence
Collect surrounding application logs, relevant deployment configuration, dependency-side evidence and a known-good comparison. Preserve timestamps when present and label absent timestamps as unknown. Record evidence that contradicts a proposed cause as well as evidence supporting it. If only a generic failure message is available, report insufficient evidence and request context rather than asserting a cause.

## Recovery guidance
Remove only approved disposable files or extend the verified filesystem through the operator’s process, after preserving required evidence. Avoid blanket recursive deletion. Correct retention where growth is uncontrolled. Verify available bytes and inodes, a successful write to the application path and absence of new ENOSPC failures.

## Sources
- https://docs.aws.amazon.com/ebs/latest/userguide/recognize-expanded-volume-linux.html
