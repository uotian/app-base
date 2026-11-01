import createClient from "openapi-fetch";
import type { paths } from "@/types/api";
import type { NoteInput } from "@/types/notes";
import { noteSchema, notesPageSchema } from "./notes-schema";
import {
  type Environment,
  type Greeting,
  parseEnvironment,
  parseGreeting,
} from "../../../shared/contracts";

export async function getEnvironment(): Promise<Environment> {
  return window.desktop
    ? parseEnvironment(await window.desktop.getEnvironment())
    : { kind: "web", message: "Webで動いています" };
}

export async function getGreeting(signal: AbortSignal): Promise<Greeting> {
  if (window.desktop) return parseGreeting(await window.desktop.getGreeting());
  const origin =
    process.env.NODE_ENV === "development" ? "http://127.0.0.1:8100" : "";
  const controller = new AbortController();
  const abort = () => controller.abort();
  signal.addEventListener("abort", abort);
  const timer = setTimeout(abort, 5000);
  if (signal.aborted) abort();
  try {
    const { data, response } = await createClient<paths>({
      baseUrl: origin,
    }).GET("/api/greeting/", {
      signal: controller.signal,
    });
    if (!response.ok)
      throw new Error(`APIに接続できませんでした (${response.status})`);
    return parseGreeting(data);
  } finally {
    clearTimeout(timer);
    signal.removeEventListener("abort", abort);
  }
}

function notesClient(signal?: AbortSignal) {
  if (window.desktop) throw new Error("NoteはWeb版で利用できます。");
  const client = createClient<paths>({
    baseUrl:
      process.env.NODE_ENV === "development"
        ? `http://${window.location.hostname}:8100`
        : "",
    credentials: "include",
    cache: "no-store",
    signal: signal
      ? AbortSignal.any([signal, AbortSignal.timeout(10000)])
      : AbortSignal.timeout(10000),
  });
  client.use({
    onResponse({ response }) {
      if (!response.ok) {
        if (response.status === 403)
          throw new Error("ページを再読み込みして、もう一度保存してください。");
        if (response.status === 400)
          throw new Error("入力内容を確認してください。");
        throw new Error(
          `処理できませんでした (${response.status})。再試行してください。`,
        );
      }
    },
  });
  return client;
}

export async function getNotes(page: number, signal: AbortSignal) {
  if (window.desktop) return { available: false as const };
  const { data } = await notesClient(signal).GET("/api/notes/", {
    params: { query: { page } },
  });
  return { ...notesPageSchema.parse(data), available: true as const };
}

export async function addNote(input: NoteInput, csrfToken: string) {
  const { data } = await notesClient().POST("/api/notes/", {
    params: { header: { "X-CSRFToken": csrfToken } },
    body: input,
  });
  return noteSchema.parse(data);
}
