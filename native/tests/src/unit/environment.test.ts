import { expect, it } from "vitest";
import { parseEnvironment } from "../../../../shared/contracts";
import { getEnvironment } from "../../../src/environment";

it("reports macOS only when running on macOS", () => {
  expect(getEnvironment("darwin")).toEqual({
    kind: "macos",
    message: "macOSだよ",
  });
  expect(getEnvironment("win32").kind).toBe("unsupported");
  expect(getEnvironment("linux").kind).toBe("unsupported");
  expect(parseEnvironment(getEnvironment("darwin")).kind).toBe("macos");
  expect(parseEnvironment(getEnvironment("win32")).kind).toBe("unsupported");
});
