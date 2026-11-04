import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/web",
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:8770",
    trace: "off",
    screenshot: "off",
    video: "off",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    {
      name: "mobile",
      use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" },
    },
    { name: "mobile-safari", use: { ...devices["iPhone 13"] } },
  ],
  webServer: {
    command: "python -m mnemonic_recovery serve --port 8770",
    url: "http://127.0.0.1:8770",
    reuseExistingServer: false,
  },
});
