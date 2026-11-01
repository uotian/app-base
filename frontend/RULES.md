# frontendの規約

このファイルは画面実装とWeb E2Eの正本とする。共通の実装原則・完了条件は[ルートの規約](../RULES.md)に従う。

Next.js App Router＋静的出力。Pythonが業務処理を担当し、frontendは画面・入力・表示状態を担当する。新しい機能もこの配置と方式に揃える。

## 配置

実装はすべて`src/`以下。Next.js・PostCSS・shadcn・tsconfigとアプリのpackage.jsonはfrontend直下。共通設定は[開発環境の配置](../RULES.md#開発環境の配置)に従う。`features/`や`lib/`など、同じ責務の別の置き場所を追加しない。

| 場所                     | 担当                                                                  |
| ------------------------ | --------------------------------------------------------------------- |
| `src/app/`               | Next.jsのページ・ルート・metadata・ルートlayout。画面の組み立てに限定 |
| `src/layout/`            | 共通の枠、ヘッダー、フッター、Provider。`app/layout.tsx`から利用      |
| `src/components/<機能>/` | 画面・機能を組み立てる部品。例：`status/status-panel.tsx`             |
| `src/types/`             | frontend独自の名前付き型・Props型・ambient宣言                        |
| `src/hooks/`             | 独自hooks。APIデータの取得・更新、再利用するReactの状態処理           |
| `src/utils/`             | Reactに依存しない処理。通信と環境の切り替えは当面`runtime.ts`だけ     |
| `src/ui/`                | shadcnから取得したUI。取得元の構造を保つ                              |
| `src/my-ui/`             | 独自の汎用UI。propsとイベントを受け取り、業務を知らない部品           |

共有契約の配置は[sharedの規約](../RULES.md#sharedを変更するとき)に従う。実行時の検証関数は型定義とは別であり、typesに置かない。

## 依存と機能の分け方

- `app/**/page.tsx`は画面の組み立てに限定する。そこで使う画面のコンポーネントは`src/components/<機能>/`以下に、役割が分かる名前で定義する。例：`StatusPanel`、`ProjectList`、`ProjectEditor`。page内に追加のコンポーネント、hooks、操作イベント、データ取得、業務処理を書かない。
- layout・componentsはhooks、types、utils、my-ui、uiを利用できる。別の機能のcomponentsを直接importしない。密接な一つの操作なら同じ機能として扱う。
- hooksはhooks・types・utils、utilsはutils・typesに依存できる。どちらもJSXを返さない。
- typesは型だけ。`import type`を使い、実行する処理・値を置かない。utils内の検証スキーマから型を導出するための、型だけの参照は許可する。
- my-uiとuiはcomponentsやlayoutに依存しない。表示・操作に閉じたhooksは利用できるが、業務APIを取得するhooksは使わない。後者はレビュー項目。
- 外部通信・`window.desktop`への実際のアクセスは`utils/runtime.ts`だけ。画面はhooks経由で名前の付いた操作を呼ぶ。URLやIPCチャンネルを渡させない。
- OS分岐は通信・機能の実装側に閉じ込め、画面では対応状況を見る。Webのuser agentからnative対応を判断しない。
- 権限・所有者・保存可否の最終判断はPython。frontendでの入力チェックは補助であり、サーバーの検証を代替しない。

## Next.jsとルーティング

- Web／OSアプリとも主要な画面をNext.jsのルートで分ける。大量の表示フラグで別画面を切り替えない。1ページの主目的は一つとし、一覧・詳細・編集・設定を適切に分ける。一覧の検索・絞り込みなど、同じ目的を支える操作は同じページに置いてよい。
- ダイアログは確認や短い補助操作に使う。複雑な編集画面を詰め込まない。分割したページ間でも共通の部品は再利用する。ページの主目的と名前の分かりやすさはレビューする。
- `output: "export"`、`agentRules: false`を維持する。設定やAPIはインストール済みNext.jsの`node_modules/next/dist/docs/`でも確認する。
- Server Actions、実行時Route Handlers、middleware/proxy、`next/headers`、`next/server`を使わない。ビルド時にも利用者データを取得しない。
- 実行時に増えるIDは固定ページ＋クエリで扱う。`[id]`を増やす前に静的出力で成立するか確認する。URLから受け取る値も検証する。
- 内部の通常のリンクはNext.jsのLinkを使う。戻る・再読み込み・共有で復元すべき検索条件、並び順、ページ番号はURLで管理する。URLに秘密情報を置かない。
- Client Componentは操作・hooks・ブラウザAPIが必要な範囲に置く。app全体を理由なくclient化しない。
- Client Componentも静的ビルド時に描画される。`window`、`localStorage`等をモジュール初期化・初期renderで読まない。ブラウザで実行されるeffect・イベント・Query処理で扱い、初期HTMLとの不一致を作らない。`use client`だけでブラウザ専用になるとは扱わない。
- 静的ページで`useSearchParams`を使うコンポーネントはSuspenseで囲む。画面遷移後の戻る・進む・直接アクセス・再読み込みを確認し、Next devだけで判断しない。

## 状態と非同期処理

- APIデータの取得はTanStack Queryの`useQuery`、更新は`useMutation`に統一し、独自hookとして公開する。画面に`useEffect`＋fetchの別方式を作らない。
- query keyに結果を変える条件・IDを含める。応答を別のstateへコピーしない。更新成功後に関係するqueryだけを無効化する。
- 件数が増える一覧はAPI側のページングと組み合わせる。ローカルPythonでも全件取得・全件描画を前提にしない。ページ番号／cursor、絞り込み、並び順をquery keyに含める。
- QueryClientは`layout/query-provider.tsx`でウィンドウ／タブごとに一度作る。標準は30秒fresh、focus時の自動再取得なし、自動retryなし。異なる挙動が必要なqueryには理由を添える。
- 読み込み中・成功・空・失敗・非対応を区別する。不要な空状態は形式的に追加しない。失敗時は再試行手段を用意する。
- QueryのAbortSignalをHTTPに渡し、古い応答で新しい状態を上書きしない。更新中の二重送信を防ぎ、更新を無条件に自動retryしない。
- 入力や開閉は利用箇所のuseState。複雑な状態遷移はuseReducer。計算できる値をstateとして二重に持たない。
- useEffectは外部との同期に使う。クリックに応じた処理はイベントで行う。アプリ全体の設定だけ、必要になってから専用Context等で共有する。
- Promiseはawait・return・catch等で処理する。`void`は呼び出し先が失敗を処理する場合だけに使い、その処理先がコードから分かるようにする。`void`自体を例外処理と見なさない。例：現在のQueryのrefetchはerror状態で失敗を表示する。

## フォームとエラー

- 登録・編集フォームはReact Hook Form＋Zodに統一する。フォームを実装するときに依存を追加し、用途のないサンプルフォームは増やさない。入力状態・検証・エラー表示の別方式を各画面で作らない。
- 入力スキーマは`src/utils/<機能>-schema.ts`、そのスキーマから導出した入力型は`src/types/`、フォームの画面は`src/components/<機能>/`に置く。更新処理はhooksのuseMutationを利用する。Zodの検証は入力補助であり、Pythonの検証・権限確認を省略しない。
- 入力エラーは該当欄、通信エラーは操作した場所で表示する。通知だけを出してエラーを失わない。予期しない描画エラーはNext.jsのerror.tsx等のError Boundaryで扱い、イベントや非同期処理の失敗はその処理側で扱う。
- 保存済みの値と編集中の値を分け、再取得や保存失敗で入力を消さない。未保存の変更を失う画面移動・再読み込み・アプリ終了では破棄確認を行い、取消時は変更を保持する。
- 独立した表示の取得結果を分け、一部の失敗で他の利用可能な画面まで消さない。

## UIとコードの書き方

- 画面の文言は、目的・操作・現在の状態・判断に必要な情報に絞る。求められていないキャッチコピー、励まし、導入文、飾りの英語ラベルを追加しない。
- 見出し・ラベル・ボタンで分かる内容を説明文で繰り返さない。説明を足す前に、なくても操作できるか確認する。
- 公開範囲・削除の影響・入力条件・エラーと復旧方法など、判断に必要な情報は省略せず、関係する操作の近くに短く示す。実装やテンプレートの思想はREADMEに置く。

- スタイルはTailwind＋shadcn。globals.cssはTailwindのimport、theme変数、baseに限定する。独自CSS ModulesやCSS-in-JSを追加しない。
- 同じ表示を通すだけのwrapperは作らない。
- 色などはthemeの意味付きtokenを使う。キーボード操作、ラベル、読み上げ可能な状態表示、小さい画面を保つ。
- ファイル名はkebab-case、React部品はPascalCase、通常の関数・変数はcamelCase。独自hooksはuseで始める。
- Next.js規定ファイル以外の独自コードはnamed export。型・Props型はtypesへ置く。shadcn取得コード内の型は例外。
- 型だけのimportは`import type`または`import { type ... }`にする。src内の別ディレクトリからは`@/`、同じディレクトリからは`./`でimportする。src外のsharedへの参照は相対パスを使う。shadcn取得コードのimport書式は取得元を維持する。
- anyや型アサーションで入力検証を省略しない。API・IPCの値はunknownから検証する。
- `@ts-ignore`、`@ts-nocheck`で型エラーを隠さない。やむを得ない`@ts-expect-error`には原因と適用範囲が分かる理由を書く。lint無効化も理由と最小範囲をレビューする。
- 小さい機能に必ずhook・utilsファイルを追加する必要はない。行数だけで分割せず、未使用の共通化や空の階層を作らない。重複した責務が実際に現れたときに共通化する。

## src/uiのshadcnコードを変更するとき

- `src/ui/`はshadcn CLIで取得したUI。独自UIは`src/my-ui/`へ置く。
- 現在のButtonとCardは公式registryのnew-yorkから取得。CLIバージョンはfrontendのpackage.jsonとlockfileで管理する。
- 取得先は`components.json`のaliasesに従う。追加コマンド：ルートから`pnpm --filter @app-base/frontend exec shadcn add <名前>`。追加後に配置・依存・出力差分とチェックを確認する。
- 独自の動作や見た目はprops、theme、my-uiで指定する。更新のため取得元の構造を保ち、取得コード内のProps型をtypesへ移動しない。
- Prettierの整形は行う。必要な不具合修正は理由を残し、更新時に消えていないか確認する。
- 外部I/OやNode/Electron依存を持ち込んでよいという例外ではない。

## 完了確認

実例は`app/page.tsx`→`components/status/status-panel.tsx`→`hooks/use-status.ts`→`utils/runtime.ts`。

- 自動：ARCH01–04はサーバー／通信境界。FE01–12はCSS import、Queryの利用場所、依存方向、型・hook・JSXの配置、ファイル名、exportを確認する。FE13はpageの追加コンポーネント定義・hooks・イベント・client化、FE14はsrc内のimportパス形式を検査する。shadcn取得先は設定テストでも確認する。
- 自動：PrettierはTailwindクラスも整列する。型・一般的なバグはTypeScript／ESLint、Promiseの処理漏れは型情報を使うESLint、静的出力はNext buildで確認する。型だけのimportと型エラー抑制コメントもESLintで確認する。
- レビュー：ページの主目的、名前、責務の妥当性、共通化の判断、query keyの十分性、フォーム方式、ブラウザAPIの実行タイミング、入力・権限・エラーの扱い。間接呼び出しによる外部I/Oも確認する。
- UI変更はWebとMacの実際の画面で確認する。

## テスト

共通のテスト設計・保護は[testsの規約](../tests/RULES.md)、配置・結果保存先は[共通規約](../RULES.md#テストの配置)に従う。

Web E2Eは`tests/src/e2e/`、設定は`playwright.config.ts`。`pnpm test:frontend`でビルド済み静的画面から実際のDjango APIまでを確認する。`tests/src/e2e/web-server.py`が一時SQLite DBと通常の静的Webサーバーを用意し、終了時にDBを破棄する。実行時Nextサーバーなしで動くことを確認し、Next devだけの確認で済ませない。

テストとPlaywright設定はNode上で動くため、frontendアプリの実行時Node依存禁止の対象外。`src/`への制約を緩める理由にはしない。
