"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { useNotes } from "@/hooks/use-notes";
import { useUnsavedForm } from "@/hooks/use-unsaved-form";
import type { NoteInput } from "@/types/notes";
import { Button } from "@/ui/button";
import { Card, CardContent } from "@/ui/card";
import { noteInputSchema } from "@/utils/notes-schema";

export function NotesPanel() {
  const params = useSearchParams();
  const pageValue = Number(params.get("page") ?? 1);
  const page = Number.isSafeInteger(pageValue) && pageValue > 0 ? pageValue : 1;
  const { notes, create } = useNotes(page);
  const form = useForm<NoteInput>({
    resolver: zodResolver(noteInputSchema),
    defaultValues: { text: "" },
  });
  useUnsavedForm(form.formState.isDirty);
  return (
    <section
      className="mx-auto max-w-175 space-y-6 py-12"
      aria-labelledby="notes-title"
    >
      <h1 id="notes-title" className="text-3xl font-semibold">
        Note
      </h1>
      {notes.isPending ? (
        <p role="status">Noteを読み込んでいます…</p>
      ) : notes.isError ? (
        <div role="alert">
          <p>{notes.error.message}</p>
          <Button onClick={() => void notes.refetch()}>一覧を再取得</Button>
          <Link className="ml-3 underline" href="/notes/">
            先頭に戻る
          </Link>
        </div>
      ) : !notes.data.available ? (
        <p>NoteはWeb版で利用できます。</p>
      ) : (
        <>
          <Card>
            <CardContent>
              <form
                className="space-y-3"
                onSubmit={form.handleSubmit((input) =>
                  create.mutate(input, { onSuccess: () => form.reset() }),
                )}
              >
                <label className="block font-medium" htmlFor="note-text">
                  新しいNote
                </label>
                <p
                  id="note-visibility"
                  className="text-sm text-muted-foreground"
                >
                  全員に公開
                </p>
                <textarea
                  id="note-text"
                  rows={4}
                  maxLength={2000}
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                  {...form.register("text")}
                  aria-invalid={Boolean(form.formState.errors.text)}
                  aria-describedby="note-visibility note-error"
                  disabled={create.isPending}
                />
                <p id="note-error" className="text-sm text-destructive">
                  {form.formState.errors.text?.message}
                </p>
                {create.isError && (
                  <p role="alert" className="text-sm text-destructive">
                    {create.error.message}
                  </p>
                )}
                {create.isSuccess && (
                  <p role="status" className="text-sm">
                    保存しました。
                  </p>
                )}
                <Button type="submit" disabled={create.isPending}>
                  {create.isPending ? "保存中…" : "保存"}
                </Button>
              </form>
            </CardContent>
          </Card>
          <div aria-live="polite">
            <h2 className="mb-4 font-semibold">
              保存したNote（{notes.data.count}件）
            </h2>
            {notes.data.results.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                まだNoteはありません。
              </p>
            ) : (
              <ul className="space-y-3">
                {notes.data.results.map((note) => (
                  <li key={note.id} className="rounded-xl border p-4">
                    <p className="break-words whitespace-pre-wrap">
                      {note.text}
                    </p>
                    <time
                      className="mt-3 block text-xs text-muted-foreground"
                      dateTime={note.created_at}
                    >
                      {new Date(note.created_at).toLocaleString("ja-JP")}
                    </time>
                  </li>
                ))}
              </ul>
            )}
            <nav
              aria-label="Noteのページ"
              className="mt-5 flex items-center gap-5"
            >
              {notes.data.previous && (
                <Link className="underline" href={`/notes/?page=${page - 1}`}>
                  前へ
                </Link>
              )}
              <span>{page}ページ</span>
              {notes.data.next && (
                <Link className="underline" href={`/notes/?page=${page + 1}`}>
                  次へ
                </Link>
              )}
            </nav>
          </div>
        </>
      )}
    </section>
  );
}
