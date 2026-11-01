import { defineConfig } from "@playwright/test";

export default defineConfig({
  outputDir: "tests/results/e2e",
  testDir: "tests/src/e2e",
  testMatch: "desktop.spec.ts",
  workers: 1,
  use: { trace: "retain-on-failure" },
});
