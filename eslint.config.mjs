import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";
import architecture from "./scripts/rules/architecture.mjs";

export default defineConfig([
  ...nextVitals,
  ...nextTypescript,
  globalIgnores([
    "**/node_modules/**",
    "**/.next/**",
    "**/out/**",
    "**/dist/**",
    "**/build/**",
    "**/release/**",
    "**/.venv/**",
    "**/.cache/**",
    "backend/**",
    "frontend/next-env.d.ts",
    "**/tests/results/**",
    "playwright-report/**",
  ]),
  { settings: { next: { rootDir: "frontend/" }, react: { version: "19.3" } } },
  {
    files: ["frontend/**/*.{ts,tsx}", "native/src/**/*.ts", "shared/**/*.ts"],
    ignores: ["frontend/tests/**", "frontend/playwright.config.ts"],
    plugins: { architecture },
    rules: { "architecture/boundaries": "error" },
  },
  {
    files: ["frontend/src/**/*.{ts,tsx}"],
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      "@typescript-eslint/no-floating-promises": "error",
      "@typescript-eslint/consistent-type-imports": "error",
      "@typescript-eslint/ban-ts-comment": [
        "error",
        {
          "ts-ignore": true,
          "ts-nocheck": true,
          "ts-expect-error": "allow-with-description",
          minimumDescriptionLength: 10,
        },
      ],
    },
  },
  {
    files: ["frontend/src/ui/**/*.{ts,tsx}"],
    rules: { "@typescript-eslint/consistent-type-imports": "off" },
  },
]);
