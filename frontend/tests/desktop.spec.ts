import { test, expect } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
const output = path.resolve("../docs/evidence/runtime");
fs.mkdirSync(output, { recursive: true });
const env = fs.readFileSync("../.env", "utf8");
const password = env.match(/^DEMO_PASSWORD=(.+)$/m)![1];

test("1280px desktop: keyboard input tabs and visible focus", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/");
  await page.getByLabel("Demo password").fill(password);
  await page.getByRole("button", { name: "Enter workspace" }).click();
  const upload = page.getByRole("tab", { name: "Upload", exact: true });
  await upload.focus();
  await page.keyboard.press("ArrowRight");
  const paste = page.getByRole("tab", { name: "Paste logs" });
  await expect(paste).toBeFocused();
  await expect(paste).toHaveAttribute("aria-selected", "true");
  await expect(
    page.getByRole("button", { name: "Analyse logs" }),
  ).toBeDisabled();
  expect(await paste.evaluate((e) => getComputedStyle(e).outlineStyle)).toBe(
    "solid",
  );
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > window.innerWidth,
    ),
  ).toBe(false);
  await page.screenshot({
    path: path.join(output, "desktop-paste-1280.png"),
    fullPage: true,
  });
});

test("real API: demo access, sample, upload rejection, retained failure, history", async ({
  page,
}) => {
  test.skip(
    fs.existsSync("../runtime/index/metadata.json"),
    "Missing-index state only applies before ingestion.",
  );
  await page.goto("/");
  await page.getByLabel("Demo password").fill("invalid-test-password");
  await page.getByRole("button", { name: "Enter workspace" }).click();
  await expect(page.getByRole("alert")).toContainText("didn’t match");
  await page.screenshot({
    path: path.join(output, "desktop-access.png"),
    fullPage: true,
  });
  await page.getByLabel("Demo password").fill(password);
  await page.getByRole("button", { name: "Enter workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Investigate your logs." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Load sample" }).first().click();
  await expect(page.getByText("deployment-db.log ·")).toBeVisible();
  await page.locator("input[type=file]").setInputFiles({
    name: "invalid.exe",
    mimeType: "application/octet-stream",
    buffer: Buffer.from("abc"),
  });
  await expect(page.getByRole("alert")).toContainText("can’t be read");
  await expect(page.getByText("deployment-db.log ·")).toBeVisible();
  await page.getByRole("tab", { name: "Paste logs" }).click();
  await expect(page.getByLabel("Paste UTF-8 logs")).toContainText(
    "authentication failed",
  );
  await page.getByRole("tab", { name: "Upload", exact: true }).click();
  await page.getByRole("button", { name: "Load sample" }).first().click();
  await page.screenshot({
    path: path.join(output, "desktop-investigate.png"),
    fullPage: true,
  });
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth,
  );
  expect(overflow).toBe(false);
  await page.getByRole("button", { name: "Analyse logs" }).click();
  await expect(
    page.getByRole("heading", { name: "Analysis could not be completed." }),
  ).toBeVisible({ timeout: 15000 });
  await expect(
    page.getByText(
      "Analysis is unavailable until the presenter completes service setup.",
    ),
  ).toBeVisible();
  await expect(page.getByLabel("Numbered log evidence")).toContainText(
    "[REDACTED]",
  );
  await expect(page.getByLabel("Numbered log evidence")).not.toContainText(
    "synthetic-secret",
  );
  await page.screenshot({
    path: path.join(output, "desktop-failure.png"),
    fullPage: true,
  });
  await page.getByRole("button", { name: "History", exact: true }).click();
  await expect(page.getByRole("table")).toContainText("Failed");
  await page.screenshot({
    path: path.join(output, "desktop-history.png"),
    fullPage: true,
  });
});

test("fixture report: evidence jumps, source links, download menu, desktop geometry", async ({
  page,
}) => {
  // Only this rendering check intercepts responses. No model call is claimed.
  const item = {
    id: "fixture-only",
    title: "Database authentication failed.",
    status: "completed",
    filename: "Synthetic rendering fixture",
    synthetic: true,
    created_at: "2026-10-11T14:02:00Z",
    evidence: {
      total_lines: 4,
      omitted_lines: 0,
      redactions: 1,
      lines: [
        {
          id: "L0001",
          number: 1,
          text: "14:02:00Z INFO deploy v1.8 completed",
          timestamp: "2026-10-11T14:02:00Z",
        },
        {
          id: "L0004",
          number: 4,
          text: "14:02:03Z ERROR password authentication failed for app_user",
          timestamp: "2026-10-11T14:02:03Z",
        },
      ],
    },
    retrieved_chunks: [
      {
        id: "DB-AUTH:investigation:1",
        title: "Database authentication",
        section: "Diagnostic checks",
        text: "Project-authored fixture: compare the deployed user, host and credential version without displaying secrets.",
        source_urls: [
          "https://www.postgresql.org/docs/current/client-authentication.html",
        ],
      },
    ],
    report: {
      title: "Database authentication failed.",
      summary:
        "The service logged authentication failures after a deployment. A configuration change is a hypothesis; the exact mismatch is not established.",
      analysis_status: "incident_detected",
      observed_facts: [
        {
          statement: "A deployment completed at 14:02:00 UTC.",
          log_refs: ["L0001"],
        },
        {
          statement: "The database rejected authentication for app_user.",
          log_refs: ["L0004"],
        },
      ],
      timeline: [
        {
          timestamp: "2026-10-11T14:02:00Z",
          event: "Deployment completed",
          log_refs: ["L0001"],
        },
        {
          timestamp: "2026-10-11T14:02:03Z",
          event: "Authentication failure",
          log_refs: ["L0004"],
        },
      ],
      hypotheses: [
        {
          possible_cause: "Credential or configuration mismatch",
          rank: "leading",
          log_refs: ["L0001", "L0004"],
          runbook_refs: ["DB-AUTH:investigation:1"],
          missing_evidence: [
            "Credential version, deployed environment and database authentication policy.",
          ],
          evidence_against: null,
        },
      ],
      recommended_checks: [
        {
          action: "Compare the credential source",
          why: "Authentication failed after deployment.",
          expected_observation:
            "Configured user and credential version match the intended database.",
          log_refs: ["L0004"],
          runbook_refs: ["DB-AUTH:investigation:1"],
        },
      ],
      recovery_guidance: [
        {
          proposed_action: "Correct a verified mismatch",
          prerequisites: ["Confirm the fault and obtain change approval."],
          verification_steps: ["Verify connection and health check."],
          runbook_refs: ["DB-AUTH:investigation:1"],
        },
      ],
      limitations: [
        "Synthetic rendering fixture. No live model inference was used in this test.",
        "The excerpt does not establish user impact or a proven root cause.",
      ],
    },
  };
  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    let data: unknown = {};
    if (url.pathname === "/api/session") data = { csrf_token: "fixture-token" };
    else if (url.pathname === "/api/samples") data = [];
    else if (url.pathname === "/api/incidents")
      data = { items: [item], total: 1, page: 1 };
    else data = item;
    await route.fulfill({ json: data });
  });
  await page.goto("/");
  await page.getByRole("button", { name: "History", exact: true }).click();
  await page
    .getByRole("button", { name: "Open Database authentication failed." })
    .click();
  await expect(
    page.getByRole("heading", { name: "Observed facts" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Show evidence L0004", exact: true })
    .first()
    .click();
  await expect(page.locator("#source-L0004")).toHaveClass(/highlight/);
  await expect(page.locator("#source-L0004")).toBeFocused();
  await page
    .getByRole("button", { name: "Show evidence DB-AUTH:investigation:1" })
    .first()
    .click();
  await expect(
    page.locator('[id="source-DB-AUTH:investigation:1"]'),
  ).toHaveClass(/highlight/);
  await page.getByText("Download report ↓", { exact: true }).click();
  await expect(
    page.getByRole("link", { name: "Markdown (.md)" }),
  ).toHaveAttribute("href", /format=md/);
  await expect(
    page.getByRole("link", { name: "JSON (.json)" }),
  ).toHaveAttribute("href", /format=json/);
  await page.getByText("Download report ↓", { exact: true }).click();
  await page.screenshot({
    path: path.join(output, "desktop-report-fixture.png"),
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > window.innerWidth,
    ),
  ).toBe(false);
  const columns = await page
    .locator(".report-grid")
    .evaluate((e) => getComputedStyle(e).gridTemplateColumns);
  expect(columns.split(" ")).toHaveLength(2);
});
