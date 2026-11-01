import { ESLint } from "eslint";
import { readFile } from "node:fs/promises";
import { expect, it } from "vitest";

// 構文ルールの仮想ファイルはtsconfig外。型情報を使うルールは実在パスで別に検査する。
const eslint = new ESLint({
  overrideConfig: {
    languageOptions: { parserOptions: { projectService: false } },
    rules: { "@typescript-eslint/no-floating-promises": "off" },
  },
});
const typedEslint = new ESLint();

it.each([
  ["frontend/src/components/example.ts", 'import fs from "node:fs";'],
  ["frontend/src/components/example.ts", 'import { app } from "electron";'],
  [
    "frontend/src/components/example.ts",
    'import { cookies } from "next/headers";',
  ],
  [
    "frontend/src/components/example.ts",
    'export { x } from "../../../native/src/main";',
  ],
  ["frontend/src/components/example.ts", 'fetch("/api/greeting/");'],
  ["frontend/src/components/example.ts", 'window["desktop"].getEnvironment();'],
  [
    "frontend/src/components/example.ts",
    '"use server"; export async function action() {}',
  ],
  ["frontend/src/app/api/test/route.ts", "export function GET() {}"],
  [
    "native/src/example.ts",
    'import x from "../../frontend/src/utils/runtime";',
  ],
  ["shared/example.ts", 'import x from "../native/src/main";'],
])(
  "rejects an intentional boundary violation in %s: %s",
  async (filePath, code) => {
    const [result] = await eslint.lintText(code, { filePath });
    expect(
      result.messages.some(
        (message) => message.ruleId === "architecture/boundaries",
      ),
    ).toBe(true);
  },
);

it("allows I/O at the declared runtime boundary", async () => {
  const [result] = await eslint.lintText(
    'export const load = () => fetch("/api/greeting/");',
    { filePath: "frontend/src/utils/runtime.ts" },
  );
  expect(
    result.messages.filter(
      (message) => message.ruleId === "architecture/boundaries",
    ),
  ).toEqual([]);
});

it.each([
  [
    "frontend/src/app/page.tsx",
    '"use client"; export default function Page() { return null; }',
    "FE13",
  ],
  [
    "frontend/src/app/items/page.tsx",
    "function ItemList() { return <div />; } export default function Page() { return <ItemList />; }",
    "FE13",
  ],
  [
    "frontend/src/app/page.tsx",
    "const Panel = () => <div />; export default function Page() { return <Panel />; }",
    "FE13",
  ],
  [
    "frontend/src/app/page.tsx",
    'import { useState } from "react"; export default function Page() { useState(0); return null; }',
    "FE13",
  ],
  [
    "frontend/src/app/page.tsx",
    'import * as React from "react"; export default function Page() { React.useState(0); return null; }',
    "FE13",
  ],
  [
    "frontend/src/app/page.tsx",
    "export default function Page() { return <button onClick={() => {}}>save</button>; }",
    "FE13",
  ],
  [
    "frontend/src/hooks/use-example.ts",
    'import { getGreeting } from "../utils/runtime";',
    "FE14",
  ],
  [
    "frontend/src/layout/example.tsx",
    'import { QueryProvider } from "@/layout/query-provider";',
    "FE14",
  ],
  [
    "frontend/src/types/example.ts",
    'import { schema } from "@/utils/example-schema";',
    "FE03",
  ],
  [
    "frontend/src/utils/example.ts",
    'import { useState } from "react";',
    "FE03",
  ],
  ["frontend/example.ts", "export const value = 1;", "FE08"],
  ["frontend/src/types/example.ts", "export enum Value { A, B }", "FE10"],
  [
    "frontend/src/hooks/example.tsx",
    "export function useExample() { return <>text</>; }",
    "FE12",
  ],
  [
    "frontend/src/components/orders/list.tsx",
    'import { Detail } from "@/components/users/detail";',
    "FE05",
  ],
  [
    "frontend/src/components/status/example.tsx",
    'import { getGreeting } from "@/utils/runtime";',
    "FE04",
  ],
  [
    "frontend/src/my-ui/example.tsx",
    'import { Panel } from "@/components/status/panel";',
    "FE03",
  ],
  [
    "frontend/src/utils/example.ts",
    'import { useStatus } from "@/hooks/use-status";',
    "FE03",
  ],
  [
    "frontend/src/hooks/example.tsx",
    "export function useExample() { return <div />; }",
    "FE12",
  ],
  [
    "frontend/src/components/example.tsx",
    "type Props = { name: string };",
    "FE06",
  ],
  [
    "frontend/src/components/example.tsx",
    "export function Example(props: { name: string }) { return null; }",
    "FE06",
  ],
  [
    "frontend/src/components/example.ts",
    "export function useExample() {}",
    "FE07",
  ],
  [
    "frontend/src/features/example.tsx",
    "export const Example = () => null;",
    "FE08",
  ],
  [
    "frontend/src/components/ExamplePanel.tsx",
    "export const Example = () => null;",
    "FE09",
  ],
  ["frontend/src/types/example.ts", "export const value = 1;", "FE10"],
  [
    "frontend/src/types/example.ts",
    'import { useState } from "react";',
    "FE10",
  ],
  [
    "frontend/src/components/example.tsx",
    "export default function Example() { return null; }",
    "FE11",
  ],
  [
    "frontend/src/components/example.tsx",
    'import "./example.module.css";',
    "FE01",
  ],
  [
    "frontend/src/components/example.tsx",
    'import { useQuery } from "@tanstack/react-query";',
    "FE02",
  ],
])("rejects %s: %s (%s)", async (filePath, code, rule) => {
  const [result] = await eslint.lintText(code, { filePath });
  expect(
    result.messages.some(
      (message) =>
        message.ruleId === "architecture/boundaries" &&
        message.message.startsWith(rule),
    ),
  ).toBe(true);
});

it.each([
  [
    "frontend/src/app/items/page.tsx",
    'import { Suspense } from "react"; import { StatusPanel } from "@/components/status/status-panel"; export default function Page() { return <Suspense fallback={null}><StatusPanel /></Suspense>; }',
  ],
  [
    "frontend/src/app/page.tsx",
    'import { StatusPanel } from "@/components/status/status-panel"; const Page = () => <StatusPanel />; export default Page;',
  ],
  [
    "frontend/src/layout/example.tsx",
    'import { QueryProvider } from "./query-provider";',
  ],
  [
    "frontend/src/types/example.ts",
    'import type { schema } from "@/utils/example-schema"; export type Schema = typeof schema;',
  ],
  [
    "frontend/src/types/example.ts",
    'export type { Schema } from "@/utils/example-schema";',
  ],
  [
    "frontend/src/hooks/use-example.ts",
    'import { getGreeting } from "@/utils/runtime"; export function useExample() { return getGreeting; }',
  ],
  [
    "frontend/src/my-ui/example.tsx",
    'import { Button } from "@/ui/button"; export function Example() { return <Button />; }',
  ],
  [
    "frontend/src/types/example.ts",
    'import type { ReactNode } from "react"; export type Props = { children: ReactNode };',
  ],
  [
    "frontend/src/ui/example.tsx",
    "type Props = { label: string }; export function Example({ label }: Props) { return <div>{label}</div>; }",
  ],
  [
    "frontend/src/app/page.tsx",
    "export default function Page() { return null; }",
  ],
])("allows the declared responsibility in %s", async (filePath, code) => {
  const [result] = await eslint.lintText(code, { filePath });
  expect(
    result.messages.filter(
      (message) => message.ruleId === "architecture/boundaries",
    ),
  ).toEqual([]);
});

it.each([
  ['Promise.resolve("result");', "@typescript-eslint/no-floating-promises"],
  [
    'import { StatusData } from "@/types/status"; export function value(): StatusData { return { environment: "web", greeting: "hello" }; }',
    "@typescript-eslint/consistent-type-imports",
  ],
  [
    "// @ts-ignore\nexport const value = 1;",
    "@typescript-eslint/ban-ts-comment",
  ],
  [
    "// @ts-expect-error\nexport const value = 1;",
    "@typescript-eslint/ban-ts-comment",
  ],
])("rejects unchecked TypeScript: %s", async (code, rule) => {
  const [result] = await typedEslint.lintText(code, {
    filePath: "frontend/src/utils/runtime.ts",
  });
  expect(result.messages.some((message) => message.ruleId === rule)).toBe(true);
});

it("allows handled promises and type-only imports", async () => {
  const [result] = await typedEslint.lintText(
    'import type { StatusData } from "@/types/status"; export async function value(): Promise<StatusData> { await Promise.resolve(); return { environment: "web", greeting: "hello" }; }',
    { filePath: "frontend/src/utils/runtime.ts" },
  );
  expect(result.messages).toEqual([]);
});

it("keeps shadcn additions in the agreed directories", async () => {
  const config = JSON.parse(
    await readFile(
      new URL("../../../frontend/components.json", import.meta.url),
      "utf8",
    ),
  );
  expect(config.aliases).toMatchObject({
    ui: "@/ui",
    components: "@/components",
    hooks: "@/hooks",
  });
  expect(config.tailwind.css).toBe("src/app/globals.css");
});

it.each([
  "frontend/tests/src/e2e/example.spec.ts",
  "frontend/playwright.config.ts",
])("allows Node APIs in test infrastructure: %s", async (filePath) => {
  const [result] = await eslint.lintText(
    'import { resolve } from "node:path"; export const directory = resolve(".");',
    { filePath },
  );
  expect(result.messages).toEqual([]);
});
