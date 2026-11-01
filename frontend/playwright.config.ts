import { resolve } from "node:path";
import { defineConfig } from "@playwright/test";

export default defineConfig({
  outputDir: "tests/results/e2e",
  testDir: "tests/src/e2e",
  testMatch: "web.spec.ts",
  use: { baseURL: "http://127.0.0.1:8000", trace: "retain-on-failure" },
  webServer: {
    cwd: resolve(import.meta.dirname, ".."),
    command:
      "uv run --env-file python.env python frontend/tests/src/e2e/web-server.py",
    url: "http://127.0.0.1:8000",
    reuseExistingServer: false,
    gracefulShutdown: { signal: "SIGTERM", timeout: 10000 },
  },
});
