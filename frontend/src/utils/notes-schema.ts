import { z } from "zod";
import type { components } from "@/types/api";

export const noteInputSchema = z.object({
  text: z
    .string()
    .trim()
    .min(1, "本文を入力してください")
    .max(2000, "2,000文字以内で入力してください"),
}) satisfies z.ZodType<components["schemas"]["NoteInputRequest"]>;
export const noteSchema = z.object({
  id: z.number().int().positive(),
  text: z.string(),
  created_at: z.iso.datetime({ offset: true }),
}) satisfies z.ZodType<components["schemas"]["Note"]>;
export const notesPageSchema = z.object({
  csrfToken: z.string().min(1),
  count: z.number().int().nonnegative(),
  next: z.string().nullable(),
  previous: z.string().nullable(),
  results: z.array(noteSchema),
}) satisfies z.ZodType<components["schemas"]["NotePage"]>;
