# App Base

`app-base` は、Next.js・Django・Electron・MCPを組み合わせたアプリ開発の土台です。画面と配布アプリの表示名は `App Base` です。

Django＋DRF、Next.js、Electronで作る小さなWeb／デスクトップ共通アプリ。画面にAPIの挨拶と実行環境を表示します。Web版ではNoteの一覧・追加も利用できます。

- Web：`Webで動いています`
- macOSのElectron：`macOSだよ`
- その他のElectron：`このOSのネイティブ機能は未対応です`

macOS判定にはElectronの`process.platform`を使います。別のSwift/Rust実装は必要になってから追加します。Web版は、閲覧端末やサーバーのOSにかかわらずWebとして扱います。

## 始める

Node.js 24、pnpm 11.25.0、uvが必要です。Python 3.13はuvが用意します。

```sh
pnpm install --frozen-lockfile
pnpm setup:tools
uv run --env-file python.env python backend/manage.py migrate
pnpm setup:admin
pnpm dev
```

開発画面は <http://127.0.0.1:3100>。Next devの画面更新とDjango runserverの自動再読み込みを使います。Python APIは <http://127.0.0.1:8100/api/greeting/>。開発時だけこの2つのoriginを接続します。

エディタもプロジェクトのTypeScriptを使います。VS Code系ではルートを開き、TypeScriptファイルから`TypeScript: Select TypeScript Version`でワークスペース版を選びます。エディタとCLIで診断が違う場合は、バージョン・対象のtsconfig・型定義を確認してください。

開発コマンドはリポジトリのルートで実行します。Pythonの`pyproject.toml`・`uv.lock`・`.python-version`・`.venv`と、JavaScriptのバージョン・lockfile・共通ツール設定をルートで管理します。Pythonのインタープリタもルートの`.venv`を選びます。各アプリのpackage.jsonやNext.js等の固有設定は各ディレクトリに置きます。

Pythonのバイトコードキャッシュは`python.env`で`.cache/python/`に集約しています。標準のpnpmコマンドと開発時のElectronが読み込みます。Pythonやpytestなどを直接使う場合も、ルートから`uv run --env-file python.env python …`、`pnpm test:backend`・`pnpm test:mcp`のように実行してください。エディタから起動する場合も同じ環境変数を設定します。mypy・pytest・Ruffのキャッシュも`.cache/`以下に集約しています。mypy・pytestの設定は各アプリの`mypy.ini`・`pytest.ini`、共通の型チェックオプションと実行コマンドはルートのpackage.jsonで管理します。backendとMCPのテスト・型チェックは別プロセスで実行し、それぞれの`src/`だけをimport起点にします。キャッシュは削除しても再生成されます。

## Webとして動かす

開発サーバーを停止してから：

```sh
pnpm build
pnpm start:web
```

<http://127.0.0.1:8000> を開きます。Nextの静的出力とPython APIをWaitress＋WhiteNoiseで同じoriginから配信し、Next.jsサーバーは起動しません。

Linuxでも同じ起動方法です。コンテナなどで外部にlistenする必要がある場合は、例えば以下を使います。

```sh
DJANGO_ALLOWED_HOSTS=app.example.com uv run --env-file python.env python backend/src/server.py --host 0.0.0.0 --port 8000
```

実際の公開時はTLS／reverse proxyとホスト名を環境に合わせて設定します。Web版のDjango Adminはログインが必要です。本番では`DJANGO_SECRET_KEY`を秘密の環境変数として固定してください。未設定時は開発用の一時キーとなり、プロセスの再起動でログインが無効になります。TLS配下ではセッション・CSRF CookieのSecure設定も適用してください。

## SQLiteとDjango Admin

メモの管理画面は開発時 <http://127.0.0.1:8100/admin/>、ビルド後のWeb版は <http://127.0.0.1:8000/admin/> です。`pnpm setup:admin` はルートの `.env.local` にある `DJANGO_SUPERUSER_USERNAME`・`DJANGO_SUPERUSER_PASSWORD`・`DJANGO_SUPERUSER_EMAIL` を読み込み、非対話で管理ユーザーを作成します。初回実行前にこの3項目を設定してください。`.env.local` はGit管理対象外です。作成は初回だけ実行し、既存ユーザーがいる場合はエラーになります。環境変数を書き換えても既存ユーザーは更新されません。Web画面の「Note」はログイン不要で、誰でもすべてのNoteを閲覧・追加できます。Adminのログインとは独立した公開サンプルです。

`Note`は本文（必須・最大2,000文字）、作成日時、自動採番IDを持ちます。既存のNoteも含めて全員共通の公開データです。個人情報・秘密情報は保存しないでください。編集・削除はAdminにログインし、Noteのモデル権限を持つstaffまたはsuperuserが行います。認証・セッション等のDjango標準テーブルもmigrationで作成します。所有者列を取り除くmigrationは、本文・ID・作成日時を保持します。

SQLiteの既定の保存先はルートの`db.sqlite3`（Git管理対象外）。Web運用では`DJANGO_DB_PATH`で永続ディスク上のファイルを指定し、親ディレクトリを事前に用意します。同じ設定をmigration・ユーザー作成・サーバー起動に渡してください。既存DBは削除せず`migrate`で更新します。バックアップ対象はDBであり、build成果物ではありません。

### Note API

- `GET /api/notes/?page=1`：全Noteを新しい順で20件ずつ取得（count / next / previous / results / csrfToken）。
- `POST /api/notes/`：本文 `text` を送って追加。応答はid / text / created_at。

認証は不要ですが、他サイトからの意図しない投稿を防ぐため、追加時はGETで受け取ったCookieと`X-CSRFToken`を送ります。本文は空白だけを拒否し、最大2,000文字。更新・削除APIはありません。開発時のCookie付き通信とCSRFを許可するoriginはNext devのlocalhost/127.0.0.1:3100だけです。公開運用時は匿名投稿の運用に応じて投稿制限等を設計してください。未保存入力のリンク移動・再読み込みには破棄確認を出します。ブラウザの戻る/進むの確認にはNavigation API対応ブラウザが必要です。

AdminのCSS等は`pnpm dev:backend`と`pnpm build`が`collectstatic`で生成します。直接runserverを使う場合も先に`pnpm build:static`を実行してください。

Admin・Note APIはWeb版専用で、Electron起動時には公開しません。Note画面は非対応と表示します。デスクトップのDB保存先はElectronの`userData`配下に設定しますが、現在の画面はメモを読み書きせず、デスクトップ用DBの初期化も行いません。

## MCPからNoteを使う

公式Python SDK v2の独立したHTTPサーバーです。Web版のDjango APIを起動してから、別ターミナルで実行します。

```sh
pnpm start:mcp
# ビルド済みWeb版（8000番）に接続する場合
pnpm start:mcp --api-url http://127.0.0.1:8000
```

接続先は `http://127.0.0.1:8200/mcp`（Streamable HTTP）。`list_notes(page=1)`で一覧、`add_note(text="メモ")`で追加できます。Web画面と同じ公開Noteを扱い、DBには直接アクセスしません。APIのCookieとCSRFトークンはMCP内部で扱います。追加は自動再試行しないため、通信失敗時は一覧を確認してから再実行してください。

現在はローカル開発向けにloopbackで待ち受けます。外部公開用のTLS・認証・reverse proxy設定は含みません。Web版専用で、ElectronはMCPを起動・同梱しません。SDKとHTTPクライアントの依存もルートのPython環境で管理します。

## Macアプリとして動かす

```sh
pnpm build
pnpm start:desktop
```

ElectronがPythonを自動起動し、空いているloopback portで同じ画面を開きます。APIは起動ごとのtokenで保護し、tokenはrendererに渡さずmainからAPIを呼びます。アプリ終了でPythonも停止し、Electronの異常終了時もstdin切断を検知します。

### Pythonを同梱した.appを作る

Macで実行します。

```sh
pnpm package:mac
```

Apple Siliconでは`native/release/mac-arm64/App Base.app`に出力します。Intel Macは`mac/`です。PyInstallerのディレクトリ形式でPythonと依存を同梱し、Electron Builderで.appにまとめます。利用者のPythonやuvは不要です。

旧名のHello Templateから更新する場合、Electronの標準データ保存先はApp Base用に変わります。旧保存先のデータは削除・自動移行しません。必要なデータは旧版・新版を終了してからバックアップし、新しい保存先へ引き継いでください。署名・公証・DMG配布・自動更新は未実装です。

同梱したアプリを自動確認する例：

```sh
DESKTOP_EXECUTABLE="$PWD/native/release/mac-arm64/App Base.app/Contents/MacOS/App Base" pnpm test:desktop
```

## Admin拡張

Unfold、import-export（CSV／xlsx）、simple-history、admin-sortable2をNote管理へ組み込み、DRF向けにdjango-filterを標準設定しています。公開NoteのAPI・表示順は変更しません。既存DBには`uv run --env-file python.env python backend/manage.py migrate`を適用してください。操作・権限・履歴・Admin内の並び順は[Admin拡張とNote管理](docs/django/admin/index.mdx)を参照してください。

## API仕様

Django＋DRF＋drf-spectacularを標準構成とし、`pnpm schema:generate`でOpenAPIを生成・検証します。Web起動後は`/api/docs/`でSwagger UI、`/api/redoc/`でReDocを閲覧できます。設定・JSON出力・クライアント生成の方針は[REST APIとOpenAPI](docs/django/api/index.mdx)を参照してください。

## チェック

frontendのAPI通信は`openapi-fetch`と生成API型を使い、受信値は既存のZod・共有契約で実行時検証します。`date-fns`（日付処理）、`next-intl`（多言語対応）、`lucide-react`（アイコン）は依存の追加のみです。翻訳辞書・Provider・言語切り替え・Lucideアイコンの画面配置は未実装です。未使用の間はKnipの除外対象として明記し、実装で使い始めたライブラリから除外を外します。

API型の生成はopenapi-typescript、未使用コードの検出はKnipを使います。KnipはElectronのpreloadとshadcnの生成用helperを入口として登録し、取得元の構造を維持するUIのexport、生成API型、間接利用の型・lint依存を限定的に除外しています。設定と理由は`knip.jsonc`を参照してください。検出結果は用途を確認して修正し、自動削除は行いません。

```sh
pnpm typecheck:backend     # backendだけの型チェック
pnpm typecheck:mcp         # MCPだけの型チェック
pnpm test:backend          # Djangoテスト
pnpm test:mcp              # MCP → 別プロセスのDjango API（一時DB）
pnpm test:coverage         # backend・MCPの行／分岐カバレッジ（個別プロセス）
pnpm api:generate          # OpenAPIとfrontendのAPI型を再生成
pnpm api:check             # 生成API型が最新か確認
pnpm check:unused          # Knipで未使用ファイル・export・依存を確認
pnpm audit:python          # lockfileのPython依存を既知の脆弱性について検査
pnpm check                 # API型の鮮度、未使用、lint、書式、型、unit、Python、静的/desktop build
pnpm exec playwright install chromium
pnpm test:common           # 共通契約・規約チェック
pnpm test:frontend         # 一時DBでWeb → API、匿名でのNote保存・ページング
pnpm test:native           # OS判定unit＋Electron → native/API・終了確認
pnpm format                # 書式を揃える
```

`pip-audit`・`pytest-timeout`は開発依存です。`pnpm audit:python`は`uv.lock`から通常・開発・ビルド依存をハッシュ付きで`.cache/audit/requirements.txt`へ出力し、実行環境に該当する依存を検査します。lockfileは更新しません。脆弱性の検出・通信エラーは終了コードで通知し、自動修正や検出の無視は行いません。外部サービスへの通信を伴うため、通常の`pnpm check`とは別コマンドです。

backend・MCPのpytestには、fixtureの準備・後始末を含めて1テスト60秒の上限を設定しています。必要なテストのみ`@pytest.mark.timeout(120)`などで延長でき、一時的な変更は`pnpm test:backend --timeout=120`（MCPも同様）で指定できます。macOS／Linuxでは通常signal方式が使われます。signalが利用できない環境ではthread方式でプロセスごと終了するため、後始末が保証されません。個別のHTTP・子プロセスのtimeoutと終了処理も維持します。

カバレッジは`pnpm test:coverage:backend`・`pnpm test:coverage:mcp`でも個別に計測できます。対象は各`src/`全体（migration・設定・未実行ファイルを含む）で、テストコードと外部ライブラリは含めません。端末表示に加えて、各`backend/tests/results/coverage/`・`mcp/tests/results/coverage/`に`html/index.html`と`coverage.json`を保存します。生データも同じディレクトリへ分離し、再実行時にその担当の計測結果を更新します。通常の`pnpm check`には計測を追加せず、合格率の閾値も設けていません。

子Pythonプロセスはcoverageのsubprocess patch、SIGTERM終了はsigterm設定で計測します。SIGKILLなど強制終了では結果が保存されない場合があります。Web／Electron E2Eはこの計測に含めません。namespace package内の未実行ファイルも報告し、実行されたファイルだけで割合が高く見えないようにしています。

Pythonの追加ライブラリとして、`pytest-cov`と`Hypothesis`は開発依存、`pydantic-settings`・`structlog`・`Rich`は通常依存に登録しています。pytest-covは上記コマンドで利用します。既存処理への適用箇所は次のとおりです。

- `pydantic-settings`：Djangoの環境変数を`backend/src/config/environment.py`に集約。既存の変数名・カンマ区切りのホスト指定を維持し、空のDBパスは起動時に拒否します。秘密鍵・Desktop tokenは`SecretStr`で保持し、Django設定へ渡す時だけ取り出します。`.env`は自動読込せず、従来どおり起動コマンドから指定します。
- `structlog`：Web／Desktop共通サーバーの起動・停止を構造化します。標準loggingのレコードをProcessorFormatterで整形し、非TTYではstderrにJSONを出力します。イベントにはポート・Desktopモードのみを付加し、token・DBパス・投稿内容は記録しません。Django標準ログの設定は維持します。
- `Rich`：上記ログをターミナルでは読みやすく表示します。Electronとの起動時通信に使うstdoutのJSONは維持します。
- `Hypothesis`：MCPの接続先URL検証に、生成したHTTP(S) originと認証情報・パス・query・fragmentを含む不正入力を適用します。通常の`pnpm test:mcp`で実行し、再現用データは`.cache/hypothesis/`に保存します。

テスト設定はfrontend/playwright.config.ts、native/playwright.config.ts・vitest.config.mts、共通テストはルートのvitest.config.tsです。結果はそれぞれの`tests/results/`（E2Eは`e2e/`）に保存します。`pnpm test`は共通・nativeのunit、従来の`pnpm test:e2e`はWeb E2E、`pnpm test:desktop`はElectron E2Eだけを実行します。

AGENTS.mdはAI向けの作業指示と必読規約への入口です。RULES.mdはテンプレートの基盤規約で、通常のアプリ開発では変更せず、変更には利用者の明示的な指示を必要とします。実装の規約はルートと`frontend/`・`backend/`・`native/`・`mcp/`・`scripts/rules/`・`tests/`のRULES.mdの計7ファイルです。ルートのRULES.mdの「編集前に読む規約」で変更対象に対応するファイルを確認します。sharedの規約はルート、backend内部とshadcnの規約はそれぞれbackend・frontendに集約しています。ESLintの境界ルールとPythonのASTテストは、意図的な違反を検出するテストも持ちます。責務の妥当性など自動判定できない規約は人のレビューに残します。

GitHub ActionsにもLinuxでのWeb確認と、macOSでのElectron／同梱版の確認を用意しています。ローカルでの実行と、GitHub上でのCI実行は別の検証として扱ってください。

ルール改善は「実際に迷った実装／逸脱例 → 短い規約 → 自動チェック可能なら回帰テスト → 実例の修正」の順です。文書を増やすこと自体を目的にしません。

## 構成

```text
frontend/tests/src/e2e/      Web E2E・一時DBでのサーバー起動
native/tests/src/            OS判定unit・Electron E2E
tests/src/unit/             共通契約・規約チェック
frontend/src/app/             Next.jsのページ・ルートlayout
frontend/src/layout/          共通レイアウト・Query Provider
frontend/src/components/      画面・機能ごとの部品
frontend/src/types/           frontend独自型・Props型
frontend/src/hooks/           独自hooks・TanStack Queryでのデータ取得
frontend/src/utils/           Reactに依存しない処理・通信境界
frontend/src/ui/              shadcnから取得したUI
frontend/src/my-ui/           独自の汎用UI
backend/src/apps/hello/      挨拶のDjangoアプリ
backend/src/apps/notes/      Noteモデル・migration・Django Admin
backend/src/api/             DRFのAPI・URL・desktopアクセス制限
backend/src/api/views/       APIの内容ごとのHTTP受付・応答
backend/src/api/serializers/ APIの内容ごとの入出力検証
backend/src/config/          Django設定と組み立て
backend/src/lib/             外部連携等の共通処理
backend/src/utils/           外部I/Oを持たない小さな汎用関数
backend/src/server.py        共通の配信・起動境界
backend/manage.py            Django管理コマンドの入口
mcp/src/server.py         MCPサーバーの起動・登録一覧のループ実行
mcp/src/registry.py                 全機能のツール登録関数とAPI URL生成関数の一覧
mcp/src/notes/tools/list_notes.py     メモ一覧ツールの定義・API呼び出し・出力の組み立て
mcp/src/notes/tools/add_note.py       メモ追加ツールの定義・API呼び出し
mcp/src/notes/django/               共通HTTP処理・例外
mcp/src/notes/notes_api_url.py       API URLの検証・生成
mcp/src/notes/schemas.py             API応答・ツール出力の型
mcp/tests/                   MCP → HTTP APIの結合テスト
native/src/                  Electron・preload・macOS判定・Python管理
shared/contracts.ts          TypeScript側の境界契約
```

スタイルはTailwind CSS＋shadcn、APIデータの管理はTanStack Queryに統一しています。shadcnの追加は`pnpm --filter @app-base/frontend exec shadcn add <名前>`で行い、`components.json`で取得先を`src/ui`に固定しています。現行shadcnはクラス結合に公式の`cn`パッケージを使い、`utils/cn.ts`も設定上の入口として同じ関数を公開します。

配置・依存・型・hooks・exportの規約違反はESLintで検出し、意図的な違反を渡すテストでもチェックしています。`frontend/RULES.md`に、自動検査の範囲とレビューに残る判断を記載しています。

Web／OSともページは主目的ごとに分け、`app/**/page.tsx`は`src/components/`の役割が分かる名前の部品を組み立てます。page内の追加コンポーネント・hooks・イベントと、import形式・Promiseの処理漏れも検査します。Noteの追加フォームはReact Hook Form＋Zodを使います。

一般利用者向けのログイン、音声処理、Windowsの配布設定はまだ追加していません。必要な機能に合わせて規約を育てます。

backendは`src/`をimport起点とし、apiがHTTP、appsが業務処理、libが共通の外部連携、utilsが純粋な関数を担当します。内部の規約は`backend/RULES.md`に集約しています。挨拶APIとNoteのモデル・migration・業務処理・Adminが実例です。lib・utilsにダミーの関数は置いていません。

参考：[Next.js静的出力](https://nextjs.org/docs/app/guides/static-exports)、[DRF](https://www.django-rest-framework.org/)、[Electronのセキュリティ](https://www.electronjs.org/docs/latest/tutorial/security/)、[PyInstaller](https://pyinstaller.org/en/stable/)。
