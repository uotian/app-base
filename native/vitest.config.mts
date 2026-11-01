import { resolve } from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  root: import.meta.dirname,
  test: {
    include: ["tests/src/unit/**/*.test.ts"],
    reporters: ["default", "json"],
    outputFile: resolve(import.meta.dirname, "tests/results/unit.json"),
  },
});
