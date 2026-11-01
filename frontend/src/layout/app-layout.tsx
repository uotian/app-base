import Link from "next/link";
import type { LayoutProps } from "@/types/layout";
import { QueryProvider } from "./query-provider";

export function AppLayout({ children }: LayoutProps) {
  return (
    <QueryProvider>
      <div className="mx-auto flex min-h-svh max-w-260 flex-col px-6 pt-6 pb-7 sm:px-14 sm:pt-10">
        <header className="flex items-center gap-3 text-lg font-semibold">
          <span
            aria-hidden="true"
            className="grid size-9 place-items-center rounded-xl bg-primary font-serif text-2xl font-bold text-primary-foreground"
          >
            A
          </span>
          <Link href="/">App Base</Link>
          <Link href="/notes/" className="ml-auto text-sm underline">
            Note
          </Link>
        </header>
        <main className="my-auto w-full">{children}</main>
      </div>
    </QueryProvider>
  );
}
