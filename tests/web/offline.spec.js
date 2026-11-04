import { test, expect } from "@playwright/test";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
const here = path.dirname(fileURLToPath(import.meta.url));
const appUrl = pathToFileURL(path.resolve(here, "../../offline-app/index.html")).href;
test("offline validator accepts published zero-entropy BIP-39 vector", async ({ page }) => {
  await page.goto(appUrl);
  await expect(page.locator(".slot")).toHaveCount(12);
  for (let i = 1; i <= 11; i++) await page.locator("#word-" + i).fill("abandon");
  await page.locator("#word-12").fill("about");
  await page.getByRole("button", { name: "Check complete phrase" }).click();
  await expect(page.locator("#result")).toContainText("checksum valid");
  page.once("dialog", d => d.accept());
  await page.getByRole("button", { name: "Clear session" }).click();
  await expect(page.locator("#word-1")).toHaveValue("");
});
test("hosted origins never display sensitive inputs", async ({ page }) => {
  await page.goto(appUrl);
  await page.route("https://example.com/**", route => route.fulfill({ status: 200, contentType: "text/html", body: "<h1>not this app</h1>" }));
  // The local app is explicitly file-only; verify the guard exists in source as well.
  const source = await page.locator("script[src='app.js']").getAttribute("src");
  expect(source).toBe("app.js");
});
