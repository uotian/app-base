import { expect, test } from "@playwright/test";

test("static UI talks to the real Django API, without a Next.js server", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(page.getByText("Webで動いています")).toBeVisible();
  await expect(page.getByText("Django + DRF が動いています")).toBeVisible();
  expect(await page.evaluate(() => "desktop" in window)).toBe(false);
  expect(errors).toEqual([]);
  await page.screenshot({
    path: test.info().outputPath("web.png"),
    fullPage: true,
  });
});

test("failed API requests can be retried", async ({ page }) => {
  await page.route("**/api/greeting/", (route) =>
    route.fulfill({ status: 503, body: "unavailable" }),
  );
  await page.goto("/");
  await expect(page.getByText("APIに接続できませんでした (503)")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "もう一度確認する" }),
  ).toBeVisible();
  await page.unroute("**/api/greeting/");
  await page.getByRole("button", { name: "もう一度確認する" }).click();
  await expect(page.getByText("Django + DRF が動いています")).toBeVisible();
  await page.setViewportSize({ width: 375, height: 812 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});

for (const [status, message] of [
  [400, "入力内容を確認してください。"],
  [403, "ページを再読み込みして、もう一度保存してください。"],
] as const) {
  test(`Note HTTP ${status} preserves the draft and shows recovery guidance`, async ({
    page,
  }) => {
    await page.goto("/notes/");
    await expect(page.getByLabel("新しいNote")).toBeVisible();
    await page.getByLabel("新しいNote").fill("失敗時に残す本文");
    await page.route("**/api/notes/", (route) =>
      route.request().method() === "POST"
        ? route.fulfill({
            status,
            contentType: "text/html",
            body: "<h1>Error</h1>",
          })
        : route.continue(),
    );
    await page.getByRole("button", { name: "保存", exact: true }).click();
    await expect(
      page
        .getByRole("region", { name: "Note", exact: true })
        .getByRole("alert"),
    ).toHaveText(message);
    await expect(page.getByLabel("新しいNote")).toHaveValue("失敗時に残す本文");
  });
}

test("malformed successful Note responses are rejected and can be retried", async ({
  page,
}) => {
  await page.route("**/api/notes/?*", (route) =>
    route.fulfill({ json: { count: 1, results: [{ id: "invalid" }] } }),
  );
  await page.goto("/notes/");
  await expect(
    page.getByRole("region", { name: "Note", exact: true }).getByRole("alert"),
  ).toBeVisible();
  await expect(page.getByLabel("新しいNote")).toHaveCount(0);
  await page.unroute("**/api/notes/?*");
  await page.getByRole("button", { name: "一覧を再取得" }).click();
  await expect(page.getByLabel("新しいNote")).toBeVisible();
});

test("Django Admin requires login and serves its styles", async ({ page }) => {
  await page.goto("/admin/");
  await expect(page.getByLabel(/Username/)).toBeVisible();
  await expect(page.getByLabel(/Password/)).toBeVisible();
  const response = await page.request.get("/static/unfold/css/styles.css");
  expect(response.ok()).toBe(true);
  expect(response.headers()["content-type"]).toContain("text/css");
  await page.screenshot({
    path: test.info().outputPath("admin.png"),
    fullPage: true,
  });
});

test("Public Notes validate, save, retry and survive reload", async ({
  page,
  browser,
}) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Note", exact: true }).click();
  await expect(page.getByText("まだNoteはありません。")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "ログイン", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "保存", exact: true }).click();
  await expect(page.getByText("本文を入力してください")).toBeVisible();
  await page.getByLabel("新しいNote").fill("E2Eで保存したNote");
  await page.route("**/api/notes/", (route) =>
    route.request().method() === "POST"
      ? route.fulfill({ status: 503, body: "unavailable" })
      : route.continue(),
  );
  await page.getByRole("button", { name: "保存", exact: true }).click();
  await expect(
    page.getByRole("alert").filter({ hasText: "503" }),
  ).toBeVisible();
  await expect(page.getByLabel("新しいNote")).toHaveValue("E2Eで保存したNote");
  await page.unroute("**/api/notes/");
  await page.getByRole("button", { name: "保存", exact: true }).click();
  await expect(
    page.getByText("E2Eで保存したNote", { exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByText("E2Eで保存したNote", { exact: true }),
  ).toBeVisible();
  const anonymous = await browser.newContext();
  try {
    const other = await anonymous.newPage();
    await other.goto("http://127.0.0.1:8000/notes/");
    await expect(
      other.getByText("E2Eで保存したNote", { exact: true }),
    ).toBeVisible();
  } finally {
    await anonymous.close();
  }
  await page.bringToFront();
  await page.getByLabel("新しいNote").fill("未保存");
  page.once("dialog", (dialog) => dialog.dismiss());
  await page.getByRole("link", { name: "App Base" }).click();
  await expect(page.getByLabel("新しいNote")).toHaveValue("未保存");
  page.once("dialog", (dialog) => dialog.dismiss());
  await page.evaluate(() => window.history.back());
  await expect(page).toHaveURL(/\/notes\/$/);
  await expect(page.getByLabel("新しいNote")).toHaveValue("未保存");
  await page.getByLabel("新しいNote").fill("");
  await page.setViewportSize({ width: 375, height: 812 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: test.info().outputPath("notes.png"),
    fullPage: true,
  });
});

test("Note pagination survives reload and back", async ({ page }) => {
  await page.goto("/notes/");
  const response = await page.request.get("/api/notes/");
  const data: { csrfToken: string; count: number } = await response.json();
  for (let i = 0; i < 21; i++) {
    const created = await page.request.post("/api/notes/", {
      headers: { "X-CSRFToken": data.csrfToken },
      data: { text: `Page note ${i}` },
    });
    expect(created.status()).toBe(201);
  }
  await page.reload();
  await expect(
    page.getByRole("heading", { name: `保存したNote（${data.count + 21}件）` }),
  ).toBeVisible();
  await page.getByRole("link", { name: "次へ", exact: true }).click();
  await expect(page).toHaveURL(/page=2/);
  await expect(page.getByText("Page note 0", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText("Page note 0", { exact: true })).toBeVisible();
  await page.goBack();
  await expect(
    page.getByRole("link", { name: "次へ", exact: true }),
  ).toBeVisible();
});

test("Admin extensions import, export, record history and reorder the admin list", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/admin/");
  await page.getByLabel(/Username/).fill("e2e-admin");
  await page.getByLabel(/Password/).fill("test-only-admin-password");
  await page.getByRole("button", { name: /^Log in/ }).click();
  await page.goto("/admin/notes/note/");
  await page.getByRole("link", { name: /Import$/ }).click();
  await page.locator('input[type="file"]').setInputFiles({
    name: "notes.csv",
    mimeType: "text/csv",
    buffer: Buffer.from("id,text\n,Admin import first\n,Admin import second\n"),
  });
  await page.locator('select[name="format"]').selectOption("0");
  await page.getByRole("button", { name: "Submit", exact: true }).click();
  await page
    .getByRole("button", { name: "Confirm import", exact: true })
    .click();
  await expect(
    page
      .locator("#result_list tbody tr")
      .filter({ hasText: "Admin import first" }),
  ).toBeVisible();
  await page.waitForLoadState("load");
  expect(errors).toEqual([]);
  await expect(page.locator("#admin_sortable2_config")).toHaveCount(1);
  const handles = page.locator("#result_list tbody .handle");
  const reordered = page.waitForResponse((response) =>
    response.url().includes("adminsortable2_update"),
  );
  await handles.nth(0).dragTo(handles.nth(1));
  expect((await reordered).ok()).toBe(true);
  await page.reload();
  await expect(page.locator("#result_list tbody tr").first()).toContainText(
    "Admin import first",
  );
  await page
    .locator("#result_list tbody tr")
    .filter({ hasText: "Admin import first" })
    .locator("a")
    .first()
    .click();
  await page.getByRole("link", { name: /History$/ }).click();
  await expect(
    page.getByRole("cell", { name: "e2e-admin", exact: true }).first(),
  ).toBeVisible();
  await page.goto("/admin/notes/note/");
  await page.getByRole("link", { name: /Export$/ }).click();
  await page.locator('select[name="format"]').selectOption("1");
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Submit", exact: true }).click();
  expect((await download).suggestedFilename()).toMatch(/\.xlsx$/);
  await page.goto("/admin/notes/note/");
  await page.screenshot({
    path: test.info().outputPath("admin-extensions.png"),
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
