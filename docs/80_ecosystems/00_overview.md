---
title: ライブラリ一覧
order: 0
---

# ライブラリ一覧

> 2026-11-01時点の環境に基づく一覧です。

## Backend・MCP

| 分類        | ライブラリ                   | 役割                                       |
| ----------- | ---------------------------- | ------------------------------------------ |
| API・データ | Django                       | ORM・migration・認証・Admin。              |
| API・データ | Django REST Framework（DRF） | Serializer・ViewSet・RouterによるAPI実装。 |
| API・データ | drf-spectacular              | OpenAPI生成とSwagger UI・ReDoc。           |
| API・データ | django-filter                | APIの絞り込み。標準設定のみ。              |
| Admin       | django-unfold                | Adminのテーマ・UI。                        |
| Admin       | django-import-export         | CSV・Excel（xlsx）の取込・出力。           |
| Admin       | django-simple-history        | モデルの変更履歴。                         |
| Admin       | django-admin-sortable2       | Adminのドラッグ＆ドロップ並び替え。        |
| 通信・配信  | HTTPX                        | 同期・非同期HTTPクライアント。             |
| 通信・配信  | mcp                          | MCPツールを公開する公式Python SDK。        |
| 通信・配信  | django-cors-headers          | CORSの許可元を設定。                       |
| 通信・配信  | Waitress                     | WSGIサーバー。                             |
| 通信・配信  | WhiteNoise                   | 静的ファイル配信。                         |
| 設定・検証  | Pydantic                     | 型に基づくデータ検証。                     |
| 設定・検証  | pydantic-settings            | 環境変数の読込・検証。                     |
| ログ・表示  | structlog                    | 構造化ログ。                               |
| ログ・表示  | Rich                         | ターミナル表示の整形。                     |

## Frontend

| 分類           | ライブラリ                                  | 役割                                    |
| -------------- | ------------------------------------------- | --------------------------------------- |
| 画面基盤       | React・React DOM                            | 画面部品とブラウザへの描画。            |
| 画面基盤       | Next.js                                     | ルーティング・静的出力。                |
| API・状態      | TanStack Query                              | APIデータの取得・キャッシュ・更新状態。 |
| API・状態      | openapi-typescript                          | OpenAPIからTypeScript型を生成。         |
| API・状態      | openapi-fetch                               | API型を使うHTTPクライアント。           |
| フォーム・検証 | React Hook Form                             | フォームの入力・検証・送信状態。        |
| フォーム・検証 | Zod・@hookform/resolvers                    | 入力・応答の検証とフォーム連携。        |
| UI・スタイル   | shadcn・Radix UI                            | UI部品とアクセシビリティの基盤。        |
| UI・スタイル   | Tailwind CSS・PostCSS・@tailwindcss/postcss | スタイル定義・CSS生成。                 |
| UI・スタイル   | class-variance-authority・cn                | 見た目の切替・CSSクラスの組立。         |
| UI・スタイル   | tw-animate-css                              | アニメーション。                        |
| 表示補助       | date-fns                                    | 日付の整形・計算。導入のみ。            |
| 表示補助       | next-intl                                   | 翻訳・多言語表示。導入のみ。            |
| 表示補助       | lucide-react                                | アイコン。導入のみ。                    |

## 開発・検証・配布

| 分類          | ライブラリ・ツール                               | 役割                                 |
| ------------- | ------------------------------------------------ | ------------------------------------ |
| Pythonテスト  | pytest・pytest-django                            | テスト実行・DjangoとテストDBの連携。 |
| Pythonテスト  | pytest-cov                                       | 行・分岐カバレッジ。                 |
| Pythonテスト  | Hypothesis                                       | 入力を自動生成するテスト。           |
| Pythonテスト  | pytest-timeout                                   | テストのタイムアウト。               |
| Python品質    | Ruff・mypy                                       | lint・整形と静的型チェック。         |
| Python品質    | django-stubs・djangorestframework-stubs・types-* | 外部ライブラリの型情報。             |
| 依存監査      | pip-audit                                        | 依存の既知の脆弱性を検査。           |
| JS/TSテスト   | Vitest・Playwright                               | ユニットテスト・Web／Electron E2E。  |
| JS/TS品質     | TypeScript・@types/*                             | 型チェック・型情報。                 |
| JS/TS品質     | ESLint・typescript-eslint・eslint-config-next    | JS/TS・Next.jsのlint。               |
| JS/TS品質     | Prettier・prettier-plugin-tailwindcss            | 書式・Tailwindクラス順の統一。       |
| JS/TS品質     | Knip                                             | 未使用ファイル・export・依存を検出。 |
| 開発起動      | concurrently                                     | frontend・backendの同時起動。        |
| Desktop・配布 | Electron・electron-builder                       | Desktop実行環境・パッケージ化。      |
| Desktop・配布 | esbuild・PyInstaller                             | Electronのビルド・Pythonの同梱。     |
