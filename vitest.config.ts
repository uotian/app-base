import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["tests/src/unit/**/*.test.{ts,mjs}"],
    reporters: ["default", "json"],
    outputFile: "tests/results/unit.json",
  },
});
