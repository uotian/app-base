import type { Environment } from "../../shared/contracts";

export function getEnvironment(platform: NodeJS.Platform): Environment {
  return platform === "darwin"
    ? { kind: "macos", message: "macOSだよ" }
    : { kind: "unsupported", message: "このOSのネイティブ機能は未対応です" };
}
