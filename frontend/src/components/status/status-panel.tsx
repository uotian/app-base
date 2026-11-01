"use client";

import { useStatus } from "@/hooks/use-status";
import { StatusItem } from "@/my-ui/status-item";
import { Button } from "@/ui/button";
import { Card, CardContent } from "@/ui/card";

export function StatusPanel() {
  const status = useStatus();

  return (
    <section
      aria-labelledby="title"
      className="mx-auto max-w-175 py-12 sm:pt-19 sm:pb-15"
    >
      <h1 id="title" className="text-3xl font-semibold">
        動作確認
      </h1>
      <Card
        className="mt-9 min-h-33 gap-0 py-2 shadow-none"
        role="status"
        aria-live="polite"
      >
        <CardContent>
          {status.isPending ? (
            <p className="py-5 text-sm leading-relaxed">
              接続を確認しています…
            </p>
          ) : status.isError ? (
            <div className="space-y-3 py-5 text-sm leading-relaxed text-destructive">
              <p>{status.error.message}</p>
              <Button
                variant="outline"
                onClick={() => void status.refetch()}
                disabled={status.isFetching}
              >
                もう一度確認する
              </Button>
            </div>
          ) : (
            <dl className="divide-y">
              <StatusItem label="実行環境" value={status.data.environment} />
              <StatusItem label="バックエンド" value={status.data.greeting} />
            </dl>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
