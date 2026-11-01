import type { Metadata } from "next";
import { AppLayout } from "@/layout/app-layout";
import type { LayoutProps } from "@/types/layout";
import "./globals.css";

export const metadata: Metadata = {
  title: "App Base",
  description: "Webとデスクトップで動く、小さなアプリ。",
};

export default function RootLayout({ children }: LayoutProps) {
  return (
    <html lang="ja">
      <body>
        <AppLayout>{children}</AppLayout>
      </body>
    </html>
  );
}
