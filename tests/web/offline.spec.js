import { test, expect } from "@playwright/test";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { readFile } from "node:fs/promises";
const here = path.dirname(fileURLToPath(import.meta.url));
const folder = path.resolve(here, "../../offline-app");
const appUrl = pathToFileURL(path.join(folder, "index.html")).href;

test("offline validator accepts published zero-entropy BIP-39 vector without network access", async ({ page, context }) => {
  const outbound = [];
  page.on("request", request => {
    if (/^https?:/i.test(request.url())) outbound.push(request.url());
  });
  await context.route(/^https?:/i, route => route.abort());
  // WebKit's offline emulation prevents file:// navigation, so block network requests first.
  await page.goto(appUrl);
  await context.setOffline(true);
  await expect(page.locator(".slot")).toHaveCount(12);
  for (let i = 1; i <= 11; i++) await page.locator("#word-" + i).fill("abandon");
  await page.locator("#word-12").fill("about");
  await page.getByRole("button", { name: "Check complete phrase" }).click();
  await expect(page.locator("#result")).toContainText("checksum valid");
  await page.locator("#word-12").fill("abandon");
  await page.getByRole("button", { name: "Check complete phrase" }).click();
  await expect(page.locator("#result")).toContainText("checksum invalid");
  page.once("dialog", d => d.accept());
  await page.getByRole("button", { name: "Clear session" }).click();
  await expect(page.locator("#word-1")).toHaveValue("");
  expect(outbound).toEqual([]);
});

test("hosted origins block secret entry even when assets load", async ({ page }) => {
  await page.route("http://local.test/**", async route => {
    const filename = new URL(route.request().url()).pathname.slice(1) || "index.html";
    if (!["index.html", "app.js", "wordlist.js", "styles.css"].includes(filename)) {
      await route.fulfill({ status: 404, body: "Not found" });
      return;
    }
    const body = await readFile(path.join(folder, filename));
    const contentType = filename.endsWith(".js") ? "text/javascript" : filename.endsWith(".css") ? "text/css" : "text/html";
    await route.fulfill({ status: 200, contentType, body });
  });
  await page.goto("http://local.test/index.html");
  await expect(page.locator("#blocked")).toBeVisible();
  await expect(page.locator("#workspace")).toBeHidden();
  await expect(page.locator("input[type=password]")).toHaveCount(0);
});
