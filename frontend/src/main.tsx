import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "@fontsource-variable/inter";
import "./style.css";

type Refs = { log_refs?: string[]; runbook_refs?: string[] };
type Chunk = {
  id: string;
  title: string;
  section: string;
  text: string;
  source_urls: string[];
};
type Line = {
  id: string;
  number: number;
  text: string;
  timestamp: string | null;
};
type Report = {
  title: string;
  summary: string;
  analysis_status: string;
  observed_facts: (Refs & { statement: string })[];
  timeline: (Refs & { timestamp: string | null; event: string })[];
  hypotheses: (Refs & {
    possible_cause: string;
    rank: string;
    missing_evidence: string[];
    evidence_against: string | null;
  })[];
  recommended_checks: (Refs & {
    action: string;
    why: string;
    expected_observation: string;
  })[];
  recovery_guidance: (Refs & {
    proposed_action: string;
    prerequisites: string[];
    verification_steps: string[];
  })[];
  limitations: string[];
};
type Incident = {
  id: string;
  title: string;
  status: string;
  created_at: string;
  filename: string;
  synthetic?: boolean;
  report?: Report;
  error?: { code: string; message: string };
  evidence?: {
    lines: Line[];
    total_lines: number;
    omitted_lines: number;
    redactions: number;
  };
  retrieved_chunks?: Chunk[];
  details?: Record<string, unknown>;
};
type Sample = {
  id: string;
  title: string;
  description: string;
  filename: string;
  text: string;
};
type History = { items: Incident[]; total: number; page: number };
const date = (value: string) =>
  new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Kolkata",
  }).format(new Date(value));
const statusLabel = (s: string) =>
  ({
    queued: "Queued",
    processing: "Processing",
    completed: "Completed",
    failed: "Failed",
  })[s] ?? s;

function App() {
  const [csrf, setCsrf] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);
  const [password, setPassword] = useState("");
  const [view, setView] = useState<"investigate" | "history" | "incident">(
    "investigate",
  );
  const [samples, setSamples] = useState<Sample[]>([]);
  const [mode, setMode] = useState<"upload" | "paste">("upload");
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [synthetic, setSynthetic] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [incident, setIncident] = useState<Incident | null>(null);
  const [history, setHistory] = useState<History>({
    items: [],
    total: 0,
    page: 1,
  });
  const [selected, setSelected] = useState("");
  const [details, setDetails] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  async function api<T>(url: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    if (csrf) headers.set("X-CSRF-Token", csrf);
    const response = await fetch(url, {
      ...init,
      headers,
      credentials: "same-origin",
    });
    if (!response.ok) {
      let message = "The service could not complete this request. Try again.";
      try {
        const body = await response.json();
        if (typeof body.detail === "string") message = body.detail;
      } catch {
        /* keep readable network error */
      }
      if (response.status === 401 && url !== "/api/session") setCsrf(null);
      throw new Error(message);
    }
    return response.json() as Promise<T>;
  }
  useEffect(() => {
    api<{ csrf_token: string }>("/api/session")
      .then((r) => setCsrf(r.csrf_token))
      .catch(() => {})
      .finally(() => setChecking(false));
  }, []);
  useEffect(() => {
    if (csrf)
      api<Sample[]>("/api/samples")
        .then(setSamples)
        .catch((e) => setError(e.message));
  }, [csrf]);
  useEffect(() => {
    if (
      view !== "incident" ||
      !incident ||
      !["queued", "processing"].includes(incident.status)
    )
      return;
    let cancelled = false;
    const timer = setTimeout(() => {
      api<Incident>(`/api/incidents/${incident.id}`)
        .then((result) => {
          if (!cancelled) {
            setIncident(result);
            setError("");
          }
        })
        .catch((e) => {
          if (!cancelled)
            setError(`${e.message} Use Reopen to check the saved job.`);
        });
    }, 2000);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [view, incident]);

  async function login(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const r = await api<{ csrf_token: string }>("/api/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      setCsrf(r.csrf_token);
      setPassword("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function navigate(next: "investigate" | "history") {
    setView(next);
    setError("");
    setSelected("");
    if (next === "history") loadHistory(1);
  }
  async function loadHistory(page: number) {
    try {
      setHistory(await api<History>(`/api/incidents?page=${page}`));
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function open(id: string) {
    setBusy(true);
    setError("");
    try {
      setIncident(await api<Incident>(`/api/incidents/${id}`));
      setView("incident");
      setSelected("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function choose(candidate: File | null) {
    if (!candidate) return;
    if (!/\.(txt|log)$/i.test(candidate.name)) {
      setError(
        "This file can’t be read. Choose a UTF-8 .txt or .log file. Your previous input is preserved.",
      );
      return;
    }
    if (candidate.size > 262144) {
      setError(
        "This file exceeds 256 KiB. Choose a smaller excerpt with the error and nearby lines.",
      );
      return;
    }
    setFile(candidate);
    setSynthetic(false);
    setError("");
  }
  function sample(s: Sample) {
    setFile(new File([s.text], s.filename, { type: "text/plain" }));
    setText(s.text);
    setMode("upload");
    setSynthetic(true);
    setError("");
    window.scrollTo({ top: 0, behavior: "instant" });
  }
  async function submit(e?: React.FormEvent, retryText?: string) {
    e?.preventDefault();
    setBusy(true);
    setError("");
    try {
      let init: RequestInit;
      if (retryText !== undefined || mode === "paste")
        init = {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: retryText ?? text }),
        };
      else {
        const form = new FormData();
        if (file) form.append("file", file);
        init = { method: "POST", body: form };
      }
      const result = await api<{ id: string }>("/api/incidents", init);
      await open(result.id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function jump(id: string) {
    setSelected(id);
    const target = document.getElementById(`source-${id}`);
    const excerpt = target?.querySelector("details");
    if (excerpt) excerpt.open = true;
    target?.scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "instant"
        : "smooth",
      block: "nearest",
    });
    target?.focus({ preventScroll: true });
  }
  function refs(item: Refs) {
    return (
      <div className="references">
        {[...(item.log_refs ?? []), ...(item.runbook_refs ?? [])].map((id) => (
          <button
            className="small"
            key={id}
            onClick={() => jump(id)}
            aria-label={`Show evidence ${id}`}
          >
            {id} →
          </button>
        ))}
      </div>
    );
  }

  if (checking)
    return (
      <main className="workspace">
        <p role="status">Opening workspace…</p>
      </main>
    );
  if (!csrf)
    return (
      <main className="access">
        <div className="wordmark">CloudLens</div>
        <form className="access-card soft" onSubmit={login}>
          <h1>Make sense of your logs.</h1>
          <p className="lead">
            Trace symptoms to evidence and useful troubleshooting guidance.
          </p>
          <label htmlFor="password">Demo password</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            aria-describedby={error ? "access-error" : undefined}
          />
          {error && (
            <p id="access-error" role="alert">
              ! {error}
            </p>
          )}
          <button className="primary full" disabled={busy}>
            {busy ? "Entering…" : "Enter workspace →"}
          </button>
          <p className="support">
            Protected classroom demo. Ask the presenter for access.
          </p>
        </form>
      </main>
    );
  const report = incident?.report;
  const active = incident && ["queued", "processing"].includes(incident.status);
  return (
    <div className="workspace">
      <header className="shell">
        <a
          href="#"
          className="wordmark"
          onClick={(e) => {
            e.preventDefault();
            navigate("investigate");
          }}
        >
          <svg
            aria-hidden="true"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="9" cy="9" r="7" />
            <path d="M14 14l8 8M9 5v8M5 9h8" />
          </svg>{" "}
          CloudLens
        </a>
        <nav aria-label="Main navigation">
          <button
            className={view !== "history" ? "primary" : ""}
            onClick={() => navigate("investigate")}
          >
            Investigate
          </button>
          <button
            className={view === "history" ? "primary" : ""}
            onClick={() => navigate("history")}
          >
            History
          </button>
          <details className="session-menu">
            <summary>Session ↓</summary>
            <div className="menu card">
              <p className="support">History belongs to this demo session.</p>
              <button
                onClick={async () => {
                  try {
                    await api("/api/session", { method: "DELETE" });
                    setCsrf(null);
                    setIncident(null);
                    setError("");
                  } catch (e) {
                    setError((e as Error).message);
                  }
                }}
              >
                Leave workspace
              </button>
            </div>
          </details>
        </nav>
      </header>
      <main>
        {error && (
          <div className="notice card" role="alert">
            <strong>! Request needs attention</strong>
            <p>{error}</p>
            {view === "incident" && incident && (
              <button onClick={() => open(incident.id)}>
                Reopen investigation
              </button>
            )}
          </div>
        )}
        {view === "investigate" && (
          <>
            <div className="page-heading">
              <h1>Investigate your logs.</h1>
              <p className="lead">
                Bring an error into focus. Get an evidence-backed report with
                possible causes and next checks.
              </p>
            </div>
            <form className="card input-card" onSubmit={submit}>
              <div
                className="segments"
                role="tablist"
                aria-label="Log input method"
              >
                {(["upload", "paste"] as const).map((m) => (
                  <button
                    key={m}
                    type="button"
                    role="tab"
                    aria-selected={mode === m}
                    className={mode === m ? "selected" : ""}
                    tabIndex={mode === m ? 0 : -1}
                    onKeyDown={(e) => {
                      if (
                        ["ArrowLeft", "ArrowRight", "Home", "End"].includes(
                          e.key,
                        )
                      ) {
                        e.preventDefault();
                        const next =
                          e.key === "Home"
                            ? "upload"
                            : e.key === "End"
                              ? "paste"
                              : mode === "upload"
                                ? "paste"
                                : "upload";
                        setMode(next);
                        const parent = e.currentTarget.parentElement;
                        (
                          parent?.children[
                            next === "upload" ? 0 : 1
                          ] as HTMLButtonElement
                        )?.focus();
                      }
                    }}
                    onClick={() => setMode(m)}
                  >
                    {m === "upload" ? "Upload" : "Paste logs"}
                  </button>
                ))}
              </div>
              {mode === "upload" ? (
                <>
                  <div
                    className="dropzone soft"
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      choose(e.dataTransfer.files[0] ?? null);
                    }}
                  >
                    <h3>Drop a log file here.</h3>
                    <p>UTF-8 .txt or .log · Up to 256 KiB</p>
                    <button
                      type="button"
                      onClick={() => fileInput.current?.click()}
                    >
                      Browse files
                    </button>
                    <input
                      ref={fileInput}
                      type="file"
                      accept=".txt,.log,text/plain"
                      hidden
                      onChange={(e) => {
                        choose(e.target.files?.[0] ?? null);
                        e.target.value = "";
                      }}
                    />
                  </div>
                  {file && (
                    <div className="file-row">
                      <p>
                        {file.name} · {(file.size / 1024).toFixed(1)} KiB
                        {synthetic && " · Synthetic sample"}
                      </p>
                      <button
                        type="button"
                        onClick={() => {
                          setFile(null);
                          setSynthetic(false);
                        }}
                      >
                        Remove
                      </button>
                    </div>
                  )}
                </>
              ) : (
                <>
                  <label htmlFor="logs" className="support">
                    Paste UTF-8 logs · Up to 256 KiB
                  </label>
                  <textarea
                    id="logs"
                    value={text}
                    onChange={(e) => {
                      setText(e.target.value);
                      setSynthetic(false);
                    }}
                    placeholder="Paste the error and surrounding log lines here."
                    rows={10}
                  />
                  <p className="support">
                    {new TextEncoder().encode(text).length.toLocaleString()}{" "}
                    bytes{synthetic && " · Synthetic sample"}
                  </p>
                </>
              )}
              <div className="form-footer">
                <p className="support">
                  Common secrets are redacted before analysis. Redaction is
                  best-effort; use synthetic data for this demo.
                </p>
                <button
                  className="primary"
                  disabled={
                    busy ||
                    (mode === "upload"
                      ? !file
                      : !text.trim() ||
                        new TextEncoder().encode(text).length > 262144)
                  }
                >
                  {busy ? "Submitting…" : "Analyse logs →"}
                </button>
              </div>
            </form>
            <section className="samples">
              <h2>Try a synthetic incident.</h2>
              <p>
                Choose a sample to load it into the input. Analysis starts when
                you select Analyse logs.
              </p>
              <div className="sample-grid">
                {samples.map((s) => (
                  <article className="card" key={s.id}>
                    <p className="support">Synthetic sample</p>
                    <h3>{s.title}</h3>
                    <p>{s.description}</p>
                    <button className="full" onClick={() => sample(s)}>
                      Load sample →
                    </button>
                  </article>
                ))}
              </div>
            </section>
          </>
        )}
        {view === "history" && (
          <>
            <div className="page-heading">
              <h1>Investigation history.</h1>
              <p className="lead">
                Reports from this demo session. Completed and failed
                investigations remain available.
              </p>
            </div>
            {history.total ? (
              <>
                <div className="card history">
                  <table>
                    <thead>
                      <tr>
                        <th>Investigation</th>
                        <th>Created (IST)</th>
                        <th>Status</th>
                        <th>Report</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.items.map((i) => (
                        <tr key={i.id}>
                          <td>
                            <strong>{i.title}</strong>
                          </td>
                          <td>{date(i.created_at)}</td>
                          <td>
                            <span className="badge">
                              {statusLabel(i.status)}
                            </span>
                          </td>
                          <td>
                            <button
                              disabled={busy}
                              onClick={() => open(i.id)}
                              aria-label={`Open ${i.title}`}
                            >
                              Open →
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="pagination">
                  <button
                    disabled={history.page <= 1}
                    onClick={() => loadHistory(history.page - 1)}
                  >
                    ← Previous
                  </button>
                  <span>Page {history.page}</span>
                  <button
                    disabled={history.page * 20 >= history.total}
                    onClick={() => loadHistory(history.page + 1)}
                  >
                    Next →
                  </button>
                </div>
              </>
            ) : (
              <div className="card soft">
                <h2>Your first investigation starts here.</h2>
                <p>
                  Submit logs or load a synthetic sample. Completed and failed
                  investigations will appear in this session.
                </p>
                <button
                  className="primary full"
                  onClick={() => navigate("investigate")}
                >
                  Investigate logs →
                </button>
              </div>
            )}
          </>
        )}
        {view === "incident" && incident && (
          <>
            <div className="page-heading report-heading">
              <div>
                <h1>
                  {report?.title ??
                    (active
                      ? "Investigation in progress."
                      : "Investigation needs attention.")}
                </h1>
                <p>
                  {incident.synthetic ? "Synthetic incident · " : ""}
                  {incident.filename} · {date(incident.created_at)} IST
                </p>
              </div>
              {report && (
                <details className="download">
                  <summary className="primary">Download report ↓</summary>
                  <div className="menu card">
                    <a
                      href={`/api/incidents/${incident.id}/download?format=md`}
                    >
                      Markdown (.md)
                    </a>
                    <a
                      href={`/api/incidents/${incident.id}/download?format=json`}
                    >
                      JSON (.json)
                    </a>
                  </div>
                </details>
              )}
            </div>
            {active && (
              <div
                className="card soft processing"
                role="status"
                aria-live="polite"
              >
                <p className="support">Submitted logs</p>
                <h3>{incident.filename}</h3>
                <h2>
                  <span className="spinner" aria-hidden="true" />{" "}
                  {statusLabel(incident.status)}
                </h2>
                <p className="support">
                  Queued → Processing → Completed or Failed
                </p>
                <p>
                  We select relevant log evidence, retrieve matching guidance
                  and validate the generated report. You can return to History
                  and reopen this investigation.
                </p>
                <button className="full" onClick={() => navigate("history")}>
                  View history
                </button>
              </div>
            )}
            {incident.error && (
              <div className="card soft">
                <p className="support">
                  Analysis · {incident.error.code.replaceAll("_", " ")}
                </p>
                <h2>Analysis could not be completed.</h2>
                <p>{incident.error.message}</p>
                <button
                  disabled={busy}
                  onClick={() =>
                    submit(
                      undefined,
                      incident.evidence?.lines.map((l) => l.text).join("\n"),
                    )
                  }
                >
                  Retry analysis
                </button>
                <p className="support">
                  Retry submits the retained, redacted excerpt as a new
                  investigation. Its line IDs are assigned again.
                </p>
              </div>
            )}
            {report && (
              <div className="report-status">
                <span className="badge">
                  {report.analysis_status === "incident_detected"
                    ? "! Incident detected"
                    : report.analysis_status === "no_incident_detected"
                      ? "No supported incident"
                      : "! Insufficient evidence"}
                </span>
                <span className="badge">Completed</span>
                <p className="support">
                  AI-assisted hypotheses require verification. Impact and exact
                  root cause may be unknown.
                </p>
              </div>
            )}
            {!active && (
              <div className={`report-grid ${report ? "" : "evidence-only"}`}>
                <div className="report-content">
                  {report && (
                    <>
                      <section>
                        <h2>Summary</h2>
                        <p>{report.summary}</p>
                      </section>
                      {report.observed_facts.length > 0 && (
                        <section className="card soft">
                          <h2>Observed facts</h2>
                          <p className="support">
                            What the supplied logs establish.
                          </p>
                          {report.observed_facts.map((f, i) => (
                            <div className="fact" key={i}>
                              <p>{f.statement}</p>
                              {refs(f)}
                            </div>
                          ))}
                        </section>
                      )}
                      {report.timeline.length > 0 && (
                        <section>
                          <h2>Timeline</h2>
                          <p className="support">
                            Times as recorded in logs. Unknown timestamps remain
                            unknown.
                          </p>
                          {report.timeline.map((t, i) => (
                            <div className="timeline-row" key={i}>
                              <time>
                                {t.timestamp
                                  ? t.timestamp
                                      .split(/[T ]/)
                                      .slice(1)
                                      .join(" ") +
                                    (/(Z|[+-]\d{2}:?\d{2})$/.test(t.timestamp)
                                      ? ""
                                      : " (zone unknown)")
                                  : "Unknown"}
                              </time>
                              <p>{t.event}</p>
                              {refs(t)}
                            </div>
                          ))}
                        </section>
                      )}
                      {report.hypotheses.length > 0 && (
                        <section>
                          <h2>Possible causes</h2>
                          {report.hypotheses.map((h, i) => (
                            <article className="card" key={i}>
                              <p className="support">
                                {h.rank === "leading"
                                  ? "Leading hypothesis"
                                  : "Alternative hypothesis"}{" "}
                                · not a confirmed root cause
                              </p>
                              <h3>{h.possible_cause}</h3>
                              {refs(h)}
                              <div className="inset soft">
                                <p>
                                  <strong>Missing evidence:</strong>{" "}
                                  {h.missing_evidence.join(" ")}
                                </p>
                                <p>
                                  <strong>Evidence against:</strong>{" "}
                                  {h.evidence_against ??
                                    "None supplied in this excerpt."}
                                </p>
                              </div>
                            </article>
                          ))}
                        </section>
                      )}
                      {report.recommended_checks.length > 0 && (
                        <section>
                          <h2>Recommended checks</h2>
                          <p className="support">
                            Investigate before changing the service.
                          </p>
                          {report.recommended_checks.map((c, i) => (
                            <article className="card" key={i}>
                              <h3>
                                {i + 1}. {c.action}
                              </h3>
                              <p>
                                <strong>Why:</strong> {c.why}
                              </p>
                              <p>
                                <strong>Expected observation:</strong>{" "}
                                {c.expected_observation}
                              </p>
                              {refs(c)}
                            </article>
                          ))}
                        </section>
                      )}
                      {report.recovery_guidance.length > 0 && (
                        <section className="card soft">
                          <h2>Recovery guidance</h2>
                          <p className="support">
                            Proposed action · never executed by CloudLens
                          </p>
                          {report.recovery_guidance.map((r, i) => (
                            <article key={i}>
                              <h3>{r.proposed_action}</h3>
                              <p>
                                <strong>Prerequisites:</strong>{" "}
                                {r.prerequisites.join(" ")}
                              </p>
                              <p>
                                <strong>Verify:</strong>{" "}
                                {r.verification_steps.join(" ")}
                              </p>
                              {refs(r)}
                            </article>
                          ))}
                        </section>
                      )}
                      <section>
                        <h2>Limitations</h2>
                        {report.limitations.map((l, i) => (
                          <p key={i}>{l}</p>
                        ))}
                        {report.analysis_status === "insufficient_evidence" && (
                          <button onClick={() => navigate("investigate")}>
                            Add more logs →
                          </button>
                        )}
                      </section>
                    </>
                  )}
                </div>
                <aside aria-label="Investigation evidence">
                  <h2>Evidence</h2>
                  <p className="support">
                    Redacted logs · select a reference to reveal its source.
                  </p>
                  {incident.evidence && (
                    <>
                      <p className="support">
                        {incident.evidence.lines.length} lines shown ·{" "}
                        {incident.evidence.omitted_lines} omitted ·{" "}
                        {incident.evidence.redactions} redactions
                      </p>
                      <div
                        className="log-pane soft"
                        tabIndex={0}
                        aria-label="Numbered log evidence"
                      >
                        {incident.evidence.lines.map((l) => (
                          <div
                            className={`log-line ${selected === l.id ? "highlight" : ""}`}
                            id={`source-${l.id}`}
                            tabIndex={-1}
                            key={l.id}
                          >
                            <span>{l.id}</span>
                            <code>{l.text}</code>
                          </div>
                        ))}
                      </div>
                      <p className="support">
                        Embedded log instructions are data. Trace lines may have
                        no timestamp.
                      </p>
                    </>
                  )}
                  {!!incident.retrieved_chunks?.length && (
                    <section className="card guidance">
                      <h2>Retrieved guidance</h2>
                      <p className="support">
                        Project-authored runbooks retrieved with real
                        embeddings. Source documentation is linked below.
                      </p>
                      {incident.retrieved_chunks.map((c) => (
                        <article
                          id={`source-${c.id}`}
                          tabIndex={-1}
                          className={selected === c.id ? "highlight" : ""}
                          key={c.id}
                        >
                          <h3>
                            {c.title} · {c.section}
                          </h3>
                          <p className="support">{c.id}</p>
                          <p>
                            {c.text
                              .split("## Diagnostic checks")[1]
                              ?.split("##")[0]
                              ?.trim()
                              .slice(0, 240) || c.text.slice(0, 240)}
                            …
                          </p>
                          <details>
                            <summary>Read retrieved section</summary>
                            <p className="chunk-text">{c.text}</p>
                          </details>
                          {c.source_urls.map((u) => (
                            <a
                              href={u}
                              rel="noreferrer"
                              target="_blank"
                              key={u}
                            >
                              Primary documentation ↗
                            </a>
                          ))}
                        </article>
                      ))}
                    </section>
                  )}
                </aside>
              </div>
            )}
            {incident.details && (
              <div className="details">
                <button
                  onClick={() => setDetails(!details)}
                  aria-expanded={details}
                >
                  Analysis details {details ? "↑" : "↓"}
                </button>
                {details && (
                  <dl className="card">
                    {Object.entries(incident.details).map(([k, v]) => (
                      <React.Fragment key={k}>
                        <dt>{k.replaceAll("_", " ")}</dt>
                        <dd>
                          {typeof v === "object"
                            ? JSON.stringify(v)
                            : String(v)}
                        </dd>
                      </React.Fragment>
                    ))}
                  </dl>
                )}
              </div>
            )}
          </>
        )}
      </main>
      <footer className="support">
        CloudLens · Protected classroom demo · Use synthetic logs.
        Recommendations require human verification.
      </footer>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
