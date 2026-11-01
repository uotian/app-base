import { Suspense } from "react";
import { NotesPanel } from "@/components/notes/notes-panel";

export default function NotesPage() {
  return (
    <Suspense fallback={<p>Noteを準備しています…</p>}>
      <NotesPanel />
    </Suspense>
  );
}
