import { resolve } from "node:path";
import { _electron as electron, expect, test } from "@playwright/test";

test("Electron starts Python, isolates native access, and stops Python on exit", async () => {
  const executablePath = process.env.DESKTOP_EXECUTABLE;
  const app = await electron.launch(
    executablePath
      ? {
          executablePath,
          env: { ...process.env, PATH: "/usr/bin:/bin:/usr/sbin:/sbin" },
        }
      : { cwd: resolve(__dirname, "../../.."), args: ["."] },
  );
  let origin = "";
  try {
    expect(await app.evaluate(({ app }) => app.isPackaged)).toBe(
      Boolean(executablePath),
    );
    const page = await app.firstWindow();
    await expect(
      page.getByText(
        process.platform === "darwin"
          ? "macOSだよ"
          : "このOSのネイティブ機能は未対応です",
      ),
    ).toBeVisible();
    await expect(page.getByText("Django + DRF が動いています")).toBeVisible();
    origin = new URL(page.url()).origin;
    expect((await fetch(`${origin}/api/greeting/`)).status).toBe(403);
    expect((await fetch(`${origin}/admin/`)).status).toBe(404);
    expect((await fetch(`${origin}/api/notes/`)).status).toBe(404);
    expect((await fetch(`${origin}/api/session/`)).status).toBe(404);
    expect(
      await page.evaluate(
        () => typeof (window as unknown as { require?: unknown }).require,
      ),
    ).toBe("undefined");
    expect(
      await page.evaluate(() => Object.keys(window.desktop ?? {}).sort()),
    ).toEqual(["getEnvironment", "getGreeting"]);
    await page.getByRole("link", { name: "Note", exact: true }).click();
    await expect(page.getByText("NoteはWeb版で利用できます。")).toBeVisible();
    await page.screenshot({
      path: test.info().outputPath("desktop.png"),
      fullPage: true,
    });
  } finally {
    await app.close();
  }
  await expect
    .poll(async () => {
      try {
        await fetch(origin, { signal: AbortSignal.timeout(500) });
        return true;
      } catch {
        return false;
      }
    })
    .toBe(false);
});

test("Python also exits when Electron is killed", async () => {
  const executablePath = process.env.DESKTOP_EXECUTABLE;
  const app = await electron.launch(
    executablePath
      ? { executablePath }
      : { cwd: resolve(__dirname, "../../.."), args: ["."] },
  );
  const child = app.process();
  try {
    const page = await app.firstWindow();
    await expect(page.getByText("Django + DRF が動いています")).toBeVisible();
    const origin = new URL(page.url()).origin;
    const exited = new Promise<void>((resolve) =>
      child.once("exit", () => resolve()),
    );
    child.kill("SIGKILL");
    await exited;
    await expect
      .poll(async () => {
        try {
          await fetch(origin, { signal: AbortSignal.timeout(500) });
          return true;
        } catch {
          return false;
        }
      })
      .toBe(false);
  } finally {
    if (child.exitCode === null && child.signalCode === null) await app.close();
  }
});
