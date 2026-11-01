import { join } from "node:path";
import {
  app,
  BrowserWindow,
  dialog,
  ipcMain,
  type IpcMainInvokeEvent,
} from "electron";
import { startBackend } from "./backend";
import { getEnvironment } from "./environment";

let backend: Awaited<ReturnType<typeof startBackend>> | undefined;
let quitting = false;

app.on("before-quit", (event) => {
  if (!quitting && backend) {
    event.preventDefault();
    quitting = true;
    void backend.stop().finally(() => app.quit());
  }
});
app.on("window-all-closed", () => app.quit());

void app
  .whenReady()
  .then(async () => {
    const root = app.isPackaged
      ? process.resourcesPath
      : join(__dirname, "../..");
    backend = await startBackend(root, app.isPackaged, app.getPath("userData"));
    const server = backend;
    const window = new BrowserWindow({
      width: 1000,
      height: 760,
      minWidth: 360,
      minHeight: 500,
      title: "App Base",
      backgroundColor: "#f5f5ef",
      webPreferences: {
        preload: join(__dirname, "preload.cjs"),
        contextIsolation: true,
        nodeIntegration: false,
        sandbox: true,
      },
    });
    function assertSender(event: IpcMainInvokeEvent) {
      if (
        event.sender !== window.webContents ||
        event.senderFrame !== window.webContents.mainFrame ||
        new URL(event.senderFrame.url).origin !== server.origin
      )
        throw new Error("Untrusted IPC sender");
    }
    ipcMain.handle("environment:get", (event) => {
      assertSender(event);
      return getEnvironment(process.platform);
    });
    ipcMain.handle("greeting:get", (event) => {
      assertSender(event);
      return server.getGreeting();
    });
    window.webContents.setWindowOpenHandler(() => ({ action: "deny" }));
    window.webContents.on("will-navigate", (event, url) => {
      if (new URL(url).origin !== server.origin) event.preventDefault();
    });
    window.webContents.session.setPermissionRequestHandler(
      (_contents, _permission, callback) => callback(false),
    );
    window.webContents.session.setPermissionCheckHandler(() => false);
    server.child.once("exit", () => {
      if (!quitting) {
        dialog.showErrorBox(
          "バックエンドが停止しました",
          "アプリを終了します。再起動してください。",
        );
        app.quit();
      }
    });
    await window.loadURL(server.origin);
  })
  .catch((error: unknown) => {
    dialog.showErrorBox(
      "起動できませんでした",
      error instanceof Error ? error.message : String(error),
    );
    app.quit();
  });
