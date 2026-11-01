# native

このファイルはElectron・Pythonのライフサイクルとデスクトップのテスト・配布の正本とする。共通の実装原則・完了条件は[ルートの規約](../RULES.md)に従う。

Electronのmain/preloadをTypeScriptで書き、esbuildでビルドする。今回はmacOS判定だけを提供する。SwiftやRustはこの機能には不要。

- `src/main.ts`：ウィンドウ、IPC登録、権限と起動・終了の組み立て。
- `src/preload.ts`：`contextBridge`による、機能ごとの小さい窓口だけを公開する。
- `src/environment.ts`：実行OSから環境情報を返す。macOS以外をmacOSと偽らない。
- `src/backend.ts`：Pythonの起動・準備完了・API呼び出し・停止をまとめる。
- rendererは`nodeIntegration: false`、`contextIsolation: true`、`sandbox: true`を維持する。
- 汎用の`invoke(channel, args)`、任意URL取得、任意ファイル操作、任意コマンド実行をrendererに公開しない。
- 全IPCで呼び出し元window・main frame・originを検証する。外部ページへの遷移と新規window、未実装の権限要求は拒否する。
- tokenはmainとPythonだけに渡し、renderer、URL、ログには渡さない。
- Python起動失敗や稼働中の終了を黙って無視しない。アプリ終了時とElectron異常終了時にPythonを残さない。
- 配布時は同梱Python実行ファイルを使う。開発端末のuvやPythonが利用者PCにあることを前提にしない。
- macOS用Pythonの成果物はMacで作る。Windows対応は実機・CIで確認してから対応済みとする。

配布物の検証はREADMEを参照。署名・公証・自動更新はまだ扱わない。

## テスト

共通のテスト設計・保護は[testsの規約](../tests/RULES.md)、配置・結果保存先は[共通規約](../RULES.md#テストの配置)に従う。

OS判定などのユニットテストは`tests/src/unit/`、E2Eは`tests/src/e2e/`。E2Eは実際のElectron→IPC→Pythonと起動・終了時の後始末を確認する。設定は`vitest.config.mts`・`playwright.config.ts`。`pnpm test:native`で両方、`pnpm test:unit:native`・`pnpm test:desktop`で個別に実行する。

ユニットテストの結果ファイルは`tests/results/unit.json`。
