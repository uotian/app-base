"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { NoteInput } from "@/types/notes";
import { addNote, getNotes } from "@/utils/runtime";

export function useNotes(page: number) {
  const client = useQueryClient();
  const notes = useQuery({
    queryKey: ["notes", page],
    queryFn: ({ signal }) => getNotes(page, signal),
  });
  const create = useMutation({
    mutationFn: (input: NoteInput) =>
      addNote(input, notes.data?.available ? notes.data.csrfToken : ""),
    onSuccess: () => client.invalidateQueries({ queryKey: ["notes"] }),
    onError: () => client.invalidateQueries({ queryKey: ["notes"] }),
  });
  return { notes, create };
}
