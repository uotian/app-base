import { describe, expect, it } from "vitest";
import { parseEnvironment, parseGreeting } from "../../../shared/contracts";

describe("contracts", () => {
  it("accepts a greeting, strips unrelated fields and rejects malformed responses", () => {
    expect(parseGreeting({ message: "hello", extra: 1 })).toEqual({
      message: "hello",
    });
    for (const value of [null, {}, { message: 1 }, "hello"])
      expect(() => parseGreeting(value)).toThrow();
  });
  it("validates environment responses", () => {
    expect(
      parseEnvironment({ kind: "web", message: "Webで動いています" }).kind,
    ).toBe("web");
    expect(() =>
      parseEnvironment({ kind: "macos", message: "Windows" }),
    ).toThrow();
  });
});
