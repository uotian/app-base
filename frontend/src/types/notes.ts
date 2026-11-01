import type { z } from "zod";
import type { noteInputSchema } from "@/utils/notes-schema";

export type NoteInput = z.infer<typeof noteInputSchema>;
