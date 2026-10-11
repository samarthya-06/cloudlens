import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("live provider: sample, report, evidence, download and history", async ({
  page,
}) => {
  test.skip(
    process.env.CLOUDLENS_LIVE !== "1",
    "Explicit live call opt-in required.",
  );
  test.setTimeout(210000);
  const password = fs
    .readFileSync("../.env", "utf8")
    .match(/^DEMO_PASSWORD=(.+)$/m)![1];
  await page.goto("/");
  await page.getByLabel("Demo password").fill(password);
  await page.getByRole("button", { name: "Enter workspace" }).click();
  await page.getByRole("button", { name: "Load sample" }).first().click();
  await page.getByRole("button", { name: "Analyse logs" }).click();
  await expect(
    page.getByRole("heading", { name: "Observed facts" }),
  ).toBeVisible({ timeout: 180000 });
  await expect(page.getByLabel("Numbered log evidence")).toContainText(
    "[REDACTED]",
  );
  await expect(page.getByLabel("Numbered log evidence")).not.toContainText(
    "synthetic-secret",
  );
  await page
    .getByRole("button", { name: /^Show evidence L/ })
    .first()
    .click();
  await expect(page.locator(".log-line.highlight")).toBeFocused();
  await page.getByText("Download report ↓", { exact: true }).click();
  const event = page.waitForEvent("download");
  await page.getByRole("link", { name: "Markdown (.md)" }).click();
  const download = await event;
  const downloadedPath = await download.path();
  expect(fs.readFileSync(downloadedPath!, "utf8")).toContain("[REDACTED]");
  await page.screenshot({
    path: "../docs/evidence/runtime/desktop-report-live.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > window.innerWidth,
    ),
  ).toBe(false);
  await page.getByRole("button", { name: "History", exact: true }).click();
  await expect(page.getByRole("table")).toContainText("Completed");
  await page
    .getByRole("button", { name: /^Open / })
    .first()
    .click();
  await expect(
    page.getByRole("heading", { name: "Observed facts" }),
  ).toBeVisible();
  await page.screenshot({ path: "../docs/evidence/runtime/desktop-report-live.png", fullPage: true });
  await page.context().storageState({ path: "../runtime/browser-session.json" });
  fs.chmodSync("../runtime/browser-session.json", 0o600);
});
