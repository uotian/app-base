"use client";

import { useEffect } from "react";

export function useUnsavedForm(dirty: boolean) {
  useEffect(() => {
    if (!dirty) return;
    // shortcut: 戻る/進むの確認はNavigation API対応ブラウザのみ。旧ブラウザ対応時に見直す。
    const navigation =
      "navigation" in window && window.navigation instanceof EventTarget
        ? window.navigation
        : null;
    const navigate = (event: Event) => {
      if (
        event.cancelable &&
        "navigationType" in event &&
        event.navigationType === "traverse" &&
        !window.confirm("入力中の内容を破棄して移動しますか？")
      )
        event.preventDefault();
    };
    const beforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    const click = (event: MouseEvent) => {
      if (!(event.target instanceof Element)) return;
      const link = event.target.closest("a[href]");
      if (link && !window.confirm("入力中の内容を破棄して移動しますか？")) {
        event.preventDefault();
        event.stopPropagation();
      }
    };
    navigation?.addEventListener("navigate", navigate);
    window.addEventListener("beforeunload", beforeUnload);
    document.addEventListener("click", click, true);
    return () => {
      navigation?.removeEventListener("navigate", navigate);
      window.removeEventListener("beforeunload", beforeUnload);
      document.removeEventListener("click", click, true);
    };
  }, [dirty]);
}
