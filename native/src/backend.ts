import { spawn } from "node:child_process";
import { randomBytes } from "node:crypto";
import { join } from "node:path";
import { createInterface } from "node:readline";
import { parseGreeting } from "../../shared/contracts";

export async function startBackend(
  root: string,
  packaged: boolean,
  dataDir: string,
) {
  const token = randomBytes(32).toString("hex");
  const command = packaged
    ? join(
        root,
        "backend",
        process.platform === "win32" ? "backend.exe" : "backend",
      )
    : "uv";
  const args = packaged
    ? []
    : [
        "run",
        "--project",
        root,
        "--env-file",
        join(root, "python.env"),
        "python",
        join(root, "backend/src/server.py"),
      ];
  args.push(
    "--desktop",
    "--port",
    "0",
    "--frontend",
    join(root, packaged ? "frontend" : "frontend/out"),
  );
  const child = spawn(command, args, {
    cwd: packaged ? undefined : root,
    env: {
      ...process.env,
      DESKTOP_TOKEN: token,
      DJANGO_DB_PATH: join(dataDir, "db.sqlite3"),
    },
    stdio: ["pipe", "pipe", "inherit"],
  });
  const origin = await new Promise<string>((resolve, reject) => {
    const lines = createInterface({ input: child.stdout });
    const timer = setTimeout(() => {
      child.kill();
      reject(new Error("Pythonの起動がタイムアウトしました"));
    }, 30000);
    const fail = (error: Error) => {
      clearTimeout(timer);
      lines.close();
      reject(error);
    };
    child.once("error", fail);
    child.once("exit", () => fail(new Error("Pythonが終了しました")));
    lines.once("line", (line) => {
      try {
        const value: unknown = JSON.parse(line);
        if (
          typeof value !== "object" ||
          value === null ||
          !("port" in value) ||
          typeof value.port !== "number" ||
          !Number.isInteger(value.port) ||
          value.port < 1 ||
          value.port > 65535
        )
          throw new Error("Pythonの起動応答が不正です");
        clearTimeout(timer);
        lines.close();
        resolve(`http://127.0.0.1:${value.port}`);
      } catch (error) {
        child.kill();
        fail(
          error instanceof Error
            ? error
            : new Error("Pythonを起動できませんでした"),
        );
      }
    });
  });
  return {
    origin,
    child,
    async getGreeting() {
      const response = await fetch(`${origin}/api/greeting/`, {
        headers: { Authorization: `Bearer ${token}` },
        signal: AbortSignal.timeout(5000),
      });
      if (!response.ok) throw new Error(`Python API error: ${response.status}`);
      return parseGreeting(await response.json());
    },
    stop(): Promise<void> {
      if (child.exitCode !== null || child.signalCode !== null)
        return Promise.resolve();
      return new Promise((resolve) => {
        const timer = setTimeout(() => {
          child.kill("SIGKILL");
        }, 8000);
        child.once("exit", () => {
          clearTimeout(timer);
          resolve();
        });
        child.stdin.end();
      });
    },
  };
}
