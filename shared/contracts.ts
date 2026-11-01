export type Greeting = { message: string };

export type Environment =
  | { kind: "web"; message: "Webで動いています" }
  | { kind: "macos"; message: "macOSだよ" }
  | { kind: "unsupported"; message: "このOSのネイティブ機能は未対応です" };

export interface DesktopBridge {
  getEnvironment(): Promise<Environment>;
  getGreeting(): Promise<Greeting>;
}

export function parseGreeting(value: unknown): Greeting {
  if (
    typeof value !== "object" ||
    value === null ||
    !("message" in value) ||
    typeof value.message !== "string"
  ) {
    throw new Error("APIの応答形式が正しくありません");
  }
  return { message: value.message };
}

export function parseEnvironment(value: unknown): Environment {
  if (
    typeof value === "object" &&
    value !== null &&
    "kind" in value &&
    "message" in value
  ) {
    if (value.kind === "web" && value.message === "Webで動いています")
      return { kind: value.kind, message: value.message };
    if (value.kind === "macos" && value.message === "macOSだよ")
      return { kind: value.kind, message: value.message };
    if (
      value.kind === "unsupported" &&
      value.message === "このOSのネイティブ機能は未対応です"
    )
      return { kind: value.kind, message: value.message };
  }
  throw new Error("実行環境の応答形式が正しくありません");
}
