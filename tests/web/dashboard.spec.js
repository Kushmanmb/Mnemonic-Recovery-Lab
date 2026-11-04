import { test, expect } from "@playwright/test";

const vector = [...Array(11).fill("abandon"), "about"];

async function open(page) {
  await page.goto("/");
  await expect(page.locator("#check")).toBeEnabled();
}
async function importWords(page, words = vector) {
  await page.locator("summary").click();
  await page.locator("#phrase").fill(words.join(" "));
  await page.locator("#import").click();
  await expect(page.locator("#phrase")).toHaveValue("");
}

test("all word counts have numbered slots without horizontal overflow", async ({
  page,
}) => {
  await open(page);
  for (const count of [12, 15, 18, 21, 24]) {
    await page.locator("#word-count").selectOption(String(count));
    await expect(page.locator(".word-slot")).toHaveCount(count);
    await expect(page.locator(".slot-number").last()).toHaveText(String(count));
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    for (const slot of await page.locator(".word-slot").all()) {
      expect(
        await slot.evaluate(
          (element) => element.scrollWidth <= element.clientWidth,
        ),
      ).toBe(true);
    }
  }
});

test("valid candidate never confirms or locks missing words", async ({
  page,
}) => {
  await open(page);
  await importWords(page);
  await page
    .getByRole("checkbox", { name: "Position 12 is missing", exact: true })
    .check();
  await page.locator("#check").click();
  await expect(page.locator("#result")).toContainText(
    "Checksum valid. Candidate only",
  );
  await expect(page.locator("#status-12")).toHaveText(
    "Candidate / unconfirmed",
  );
  await expect(
    page.getByRole("checkbox", { name: "Position 12 is missing", exact: true }),
  ).toBeChecked();
  await expect(page.locator("#locked-count")).toHaveText("0");
  await expect(page.locator("#word-12")).not.toHaveAttribute("readonly");
  await expect(page.locator("#word-12")).toHaveAttribute("type", "password");
  await expect(page.locator("#candidate-count")).toHaveText(
    "1 candidate checked",
  );
});

test("locks preserve known words during phrase import and length changes", async ({
  page,
}) => {
  await open(page);
  await page.locator("#word-1").fill("abandon");
  await page.getByRole("button", { name: "Lock word 1", exact: true }).click();
  await expect(page.locator("#word-1")).toHaveAttribute("readonly");
  await importWords(page, Array(12).fill("zoo"));
  await expect(page.locator("#word-1")).toHaveValue("abandon");
  await expect(page.locator("#word-2")).toHaveValue("zoo");
  await page.locator("#word-count").selectOption("24");
  await expect(page.locator("#word-1")).toHaveAttribute("readonly");
  await page
    .getByRole("button", { name: "Unlock word 1", exact: true })
    .click();
  await expect(page.locator("#word-1")).not.toHaveAttribute("readonly");
});

test("invalid and incomplete candidates do not reach the validator", async ({
  page,
}) => {
  let requests = 0;
  page.on("request", (request) => {
    if (request.url().endsWith("/api/validate")) requests += 1;
  });
  await open(page);
  await page.locator("#word-1").fill("notaword");
  await expect(page.locator("#word-1")).toHaveAttribute("aria-invalid", "true");
  await expect(
    page.getByRole("button", { name: "Lock word 1", exact: true }),
  ).toBeDisabled();
  await page.locator("#check").click();
  await expect(page.locator("#result")).toContainText("Every position needs");
  expect(requests).toBe(0);
});

test("checksum failures leave slot states unchanged", async ({ page }) => {
  await open(page);
  await importWords(page, Array(12).fill("abandon"));
  await page.locator("#check").click();
  await expect(page.locator("#result")).toContainText("Checksum invalid");
  await expect(page.locator("#locked-count")).toHaveText("0");
});

test("cancellation ignores a late validation response", async ({ page }) => {
  let release;
  const gate = new Promise((resolve) => {
    release = resolve;
  });
  await page.route("**/api/validate", async (route) => {
    await gate;
    await route.fulfill({ json: { checksum_valid: true } }).catch(() => {});
  });
  await open(page);
  await importWords(page);
  await page.locator("#check").click();
  await expect(page.locator("#cancel")).toBeEnabled();
  await page.locator("#cancel").click();
  release();
  await expect(page.locator("#result")).toContainText("Cancelled");
  await expect(page.locator("#candidate-count")).toHaveText(
    "0 candidates checked",
  );
  await expect(page.locator("#check")).toBeEnabled();
});

test("fixture progress is aggregate-only and does not change entered words", async ({
  page,
}) => {
  let payload;
  page.on("request", (request) => {
    if (request.url().endsWith("/api/experiment"))
      payload = request.postDataJSON();
  });
  await open(page);
  await page.locator("#load-fixture").click();
  await page.locator("#word-1").fill("zoo");
  await page.locator("#run-fixture").click();
  await expect(page.locator("#progress-status")).toHaveText("Completed");
  await expect(page.locator("#checksum-count")).toHaveText("128");
  await expect(page.locator("#match-count")).toHaveText("1");
  expect(payload).toEqual({
    fixture: "bip39-zero-128",
    missing_positions: [12],
    max_candidates: 2048,
  });
  await expect(page.locator("#word-1")).toHaveValue("zoo");
  await expect(page.locator("#status-12")).toHaveText(
    "Candidate / unconfirmed",
  );
});

test("fixture runs are bounded and cancelable", async ({ page }) => {
  await open(page);
  await page.locator("#load-fixture").click();
  await page
    .getByRole("checkbox", { name: "Position 1 is missing", exact: true })
    .check();
  await page.locator("#budget").fill("7");
  await page.locator("#run-fixture").click();
  await expect(page.locator("#progress-status")).toHaveText(
    "Budget reached / partial search",
  );
  await expect(page.locator("#progress-count")).toHaveText("7 / 7 checked");
  await page.locator("#budget").fill("100000");
  await page.locator("#run-fixture").click();
  await expect(page.locator("#cancel-fixture")).toBeEnabled();
  await page.locator("#cancel-fixture").click();
  await expect(page.locator("#progress-status")).toHaveText("Cancelled");
  await expect(page.locator("#check")).toBeEnabled();
});

test("local-only session has no persistent secrets and clears on reload", async ({
  page,
}) => {
  const remote = [];
  const logs = [];
  page.on("request", (request) => {
    if (new URL(request.url()).hostname !== "127.0.0.1")
      remote.push(request.url());
  });
  page.on("console", (entry) => logs.push(entry.text()));
  await open(page);
  await importWords(page);
  await page.locator("#check").click();
  await expect(page.locator("#result")).toContainText("Checksum valid");
  expect(
    await page.evaluate(() => [
      localStorage.length,
      sessionStorage.length,
      document.cookie,
    ]),
  ).toEqual([0, 0, ""]);
  expect(await page.evaluate(() => indexedDB.databases())).toEqual([]);
  expect(await page.evaluate(() => caches.keys())).toEqual([]);
  expect(remote).toEqual([]);
  expect(logs.join(" ")).not.toContain("abandon");
  await page.reload();
  await expect(page.locator("#word-1")).toHaveValue("");
  await importWords(page);
  await page.locator("#clear").click();
  await expect(page.locator("#word-12")).toHaveValue("");
  await expect(page.locator("#locked-count")).toHaveText("0");
});

test("reference failure disables checks without remote fallbacks", async ({
  page,
}) => {
  await page.route("**/api/reference", (route) => route.abort());
  await page.goto("/");
  await expect(page.locator("#reference-status")).toHaveText(
    "Local word list unavailable",
  );
  await expect(page.locator("#check")).toBeDisabled();
});

test("destructive layout and fixture changes require confirmation", async ({
  page,
}) => {
  await open(page);
  await page.locator("#word-count").selectOption("24");
  await page.locator("#word-24").fill("art");
  page.on("dialog", (dialog) => dialog.dismiss());
  await page.locator("#word-count").selectOption("12");
  await expect(page.locator("#word-count")).toHaveValue("24");
  await expect(page.locator("#word-24")).toHaveValue("art");
  await page.locator("#load-fixture").click();
  await expect(page.locator("#word-24")).toHaveValue("art");
});

test("failed local validation exits the busy state", async ({ page }) => {
  await page.route("**/api/validate", (route) => route.abort());
  await open(page);
  await importWords(page);
  await page.locator("#check").click();
  await expect(page.locator("#result")).toContainText(
    "Local validation unavailable",
  );
  await expect(page.locator("#progress-status")).toHaveText("Interrupted");
  await expect(page.locator("#check")).toBeEnabled();
  await expect(page.locator("#cancel")).toBeDisabled();
});

test("public fixture visual review", async ({ page }, testInfo) => {
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await open(page);
  await page.locator("#load-fixture").click();
  await page.locator("#reveal").check();
  await expect(page.locator(".word-entry svg")).toHaveCount(12);
  await expect(page.locator("#word-12")).toHaveValue("about");
  await page.screenshot({
    path: testInfo.outputPath("public-fixture.png"),
    fullPage: true,
    scale: "css",
  });
  expect(errors).toEqual([]);
});

test("320px viewport fits the full 24-word layout", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 900 });
  await open(page);
  await page.locator("#word-count").selectOption("24");
  await expect(page.locator(".word-slot")).toHaveCount(24);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});

test("hosted origins cannot accept or submit recovery inputs", async ({
  page,
}) => {
  const apiRequests = [];
  page.on("request", (request) => {
    if (new URL(request.url()).pathname.startsWith("/api/"))
      apiRequests.push(request.url());
  });
  await page.route("http://dashboard.example.test/**", async (route) => {
    const local = new URL(route.request().url());
    local.hostname = "127.0.0.1";
    local.port = "8770";
    const response = await route.fetch({ url: local.toString() });
    await route.fulfill({ response });
  });
  await page.goto("http://dashboard.example.test/");
  await expect(page.locator("#reference-status")).toHaveText(
    "Non-loopback origin blocked",
  );
  await expect(page.locator("#word-1")).toBeDisabled();
  await expect(page.locator("#phrase")).toBeDisabled();
  await expect(page.locator("#check")).toBeDisabled();
  expect(apiRequests).toEqual([]);
});
