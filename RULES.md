# このテンプレートの規約

目的は、Webとデスクトップで同じ画面・業務処理を使い、AIが追加した実装を人が追いやすくすること。依頼に必要な変更を最後まで行い、実行した確認と未確認事項を報告する。

## 編集前に読む規約

このファイルを読み、変更対象に対応する次の規約を編集前に読む。複数の担当にまたがる変更では、それぞれを読む。ルートから作業する場合も、子の規約が自動で読み込まれたと想定しない。

| 変更対象                                    | 読む規約                                                       |
| ------------------------------------------- | -------------------------------------------------------------- |
| frontendとその設定                          | `frontend/RULES.md`                                            |
| backendとその設定                           | `backend/RULES.md`                                             |
| mcpとその設定                               | `mcp/RULES.md`                                                 |
| nativeとその設定                            | `native/RULES.md`                                              |
| tests・backend/tests・mcp/tests・テスト設定 | `tests/RULES.md`（backend/tests・mcp/testsは各担当規約も読む） |
| 規約チェッカー                              | `scripts/rules/RULES.md`                                       |
| 設計文書・構成図                            | `docs/RULES.md`と、そこから参照するガイド・Schema              |
| scriptsの一般スクリプト・shared・共通設定   | このファイル。呼び出し側を変更する場合はその担当規約も読む     |

実装の規約はルートと各担当の計7ファイル、設計文書の規約は`docs/RULES.md`を正本とする。共通規則はルート、担当固有の規則は担当ディレクトリに一度だけ書き、深い階層に機械的にAGENTS.mdやRULES.mdを増やさない。

## 規約の正本

| 内容                                                             | 正本                                               |
| ---------------------------------------------------------------- | -------------------------------------------------- |
| 共通の責務・実装原則、開発環境、テスト配置・結果保存先、完了条件 | このファイル                                       |
| 画面実装、Web E2Eの構成・実行方法                                | [frontend/RULES.md](./frontend/RULES.md)           |
| Djangoの業務処理・依存方向、固有の検査設定、図の更新が必要な変更 | [backend/RULES.md](./backend/RULES.md)             |
| MCPの公開契約・通信境界・結合テスト                              | [mcp/RULES.md](./mcp/RULES.md)                     |
| Electron・Pythonのライフサイクル、デスクトップのテスト・配布     | [native/RULES.md](./native/RULES.md)               |
| テスト設計、利用者データ・プロセスの保護、成果物の取得方法       | [tests/RULES.md](./tests/RULES.md)                 |
| 規約チェッカーの実装・回帰テスト                                 | [scripts/rules/RULES.md](./scripts/rules/RULES.md) |
| 設計文書・図の形式、描き方と実装との照合                         | [docs/RULES.md](./docs/RULES.md)                   |

同じ規約を他のファイルへ再掲せず、正本の該当節を参照する。各担当には固有の制約と具体的な手順を記載する。

## 責務

| 場所        | 担当                                                     | 担当しないこと             |
| ----------- | -------------------------------------------------------- | -------------------------- |
| `frontend/` | Next.jsの画面・入力・表示状態                            | 業務処理、DB、OS操作       |
| `backend/`  | Django＋DRFのAPI・業務処理・永続化                       | 画面、Electronの実装       |
| `native/`   | Electronの起動・終了、限定したOS機能                     | 業務処理の重複実装         |
| `mcp/`      | 公式Python SDKのMCP入口・Django API呼び出し              | DB・業務処理の直接実装     |
| `scripts/`  | 開発・運用補助スクリプト。規約チェッカーは`rules/`に置く | アプリの業務処理           |
| `shared/`   | TypeScriptの境界の型・入力検証                           | アプリ実装、外部ライブラリ |

管理者向けのDjango Adminはbackend内の例外とし、一般利用者向けの画面はfrontendに置く。

Webはブラウザとサーバー、デスクトップはElectronと同梱Pythonで動く。サーバーのOSと利用者の端末を混同しない。Web版がMac上のブラウザで動いてもmacOS native対応とは扱わない。

## sharedを変更するとき

- frontend/nativeが共有する境界の型・小さい検証関数だけを置く。一方でしか使わない型・検証は使う側に置く。
- Node・Electron・React・外部ライブラリ・他のアプリの実装に依存させず、副作用を持たせない。外部入力は型アサーションで済ませず実行時に検証する。
- 共有するAPI契約を変えたら、DRF Serializer・shared・呼び出し側・契約テストを揃える。API契約の正本はbackendのコードから生成するOpenAPIとし、フロントエンドを分離する場合はOpenAPIからのTypeScript client・型生成を標準候補とする。コード生成ツールは必要になった時点で導入する。

## 開発環境の配置

- 言語バージョン、lockfile、共通の開発ツール設定と実行コマンドはルートで管理する。対象アプリ固有のmypy・pytest設定は各アプリ直下に置く。通常の開発コマンドはルートから実行する。
- Pythonの`pyproject.toml`・`uv.lock`・`.python-version`はルート。uvの環境もルートの`.venv`一つを使い、backend内に別環境を作らない。
- Pythonのバイトコードキャッシュはルートの`.cache/python/`に集約する。`python.env`の`PYTHONPYCACHEPREFIX`を起動前に読み込む。Pythonコマンドはルートから`uv run --env-file python.env …`で実行する。標準のpnpmコマンドと開発時のElectronもこの設定を使う。機能コード内で設定せず、ソース横に`__pycache__`を増やさない。`python.env`は秘密情報を入れない共通設定、`.cache/`はGit・lint・formatの対象外とする。
- mypy・pytest・Ruffのキャッシュはそれぞれルートの`.cache/mypy/`・`.cache/pytest/`・`.cache/ruff/`に置く。Ruffの保存先は`pyproject.toml`、mypyはルートの実行コマンド、pytestは各アプリの`pytest.ini`で管理する。mypy・pytestはbackend/mcpごとにキャッシュも分ける。
- backendとmcpのテスト・型チェックは別プロセスで実行し、それぞれの`src/`だけをimport起点にする。両方を同じ検索パスに追加しない。ルートの`pnpm check:python`が個別の検査をまとめて実行する。
- JavaScriptはルートの`package.json`・`pnpm-workspace.yaml`・`pnpm-lock.yaml`・`.node-version`で管理する。共通のESLint・Prettier・共有テストの設定もルートに置く。frontend/native固有のテスト設定は各アプリ直下に置く。
- frontend/nativeの`package.json`はそれぞれの依存とアプリ固有コマンドを宣言する。Next.js・PostCSS・shadcn・Electron・各アプリのtsconfigなど、対象が決まる設定は各アプリに置く。共通の言語設定とアプリ固有設定を重複させない。
- `.venv`・`node_modules`・ツールのキャッシュは生成物。管理対象にせず、lockfileから再作成する。仮想環境を別の場所へコピーして使い回さない。

## 実装の原則

- 既存の一つの実装方法に揃える。新しい方法が必要なら、理由と既存コードへの影響を説明し、規約・実例・チェックを一緒に更新する。
- 要求されていない拡張点、汎用基底クラス、DIコンテナ、Repository層、空のディレクトリを追加しない。単純な処理に機械的な多層化を強制しない。
- 関数・メソッドの内部は、上から処理を追えるように書く。外部から受け取る値の検証、権限確認、データ保護、後始末は省略しない。
- 秘密情報・利用者のデータ・開発端末固有の絶対パスをソースやログに残さない。
- 外部I/Oは境界に集める。非対応の機能は非対応として返す。別のサービスへ黙ってフォールバックしない。
- 依存追加は標準機能と既存依存で足りるか確認してから行う。依存ファイルとlockfileを同時に更新する。
- 実装変更では呼び出し側・検証・設定・設計文書を揃える。仕様の正本を確認し、古い説明を削除する。同じ仕様を複数の文書へ重複して書かない。共通の規約に個別アプリの画面仕様を混ぜない。
- エディタ・CLI・CIはlockfileで揃えたプロジェクトのTypeScriptと対象のtsconfigを使う。エディタだけに型エラーが出る場合も無視せず、使用バージョン・設定・型定義を確認する。ブラウザ／ElectronのAPI対応は型チェックとは別に確認する。

## 自動チェックと人のレビュー

静的チェックは規約のすべてを証明するものではない。新しい外部I/O手段や意図的なlint無効化はレビューで確認する。ルールを増やす理由は実際の迷い・逸脱・不具合に結び付ける。

- 型・書式・一般的なバグはTypeScript、mypy、ESLint、Ruff、Prettierで確認する。仕様の妥当性は人が確認する。
- 規約ごとの検出範囲とレビュー項目は、[frontendの完了確認](./frontend/RULES.md#完了確認)、[backendの完了確認](./backend/RULES.md#完了確認)、[MCPの自動チェックと人のレビュー](./mcp/RULES.md#自動チェックと人のレビュー)を正本とする。
- チェッカーの追加・修正と回帰テストは[規約チェッカーの規約](./scripts/rules/RULES.md)に従う。

## テストの配置

- frontend/native固有のテストは各アプリの`tests/src/`、共通契約・リポジトリ全体の規約チェックはルートの`tests/src/unit/`に置く。Pythonテストはbackend/mcpの`tests/`に置く。
- テスト変更時は対象アプリの規約と`tests/RULES.md`を読む。テスト用の深い階層にAGENTS.mdやRULES.mdを増やさない。
- JavaScriptのテスト結果は所有するディレクトリの`tests/results/`に置く。E2Eはその下の`e2e/`に分け、ユニットテストの結果を消さない。
- 実行はルートのコマンドで統一し、CIも同じ入口を使う。`pnpm test`は共通・nativeのユニットテストを実行する。アプリ別のコマンドは各担当のテスト・完了確認の節を参照する。`test:e2e`・`test:desktop`も従来の入口として維持する。

## 完了条件

- `pnpm check`：書式、lint、型、ユニットテスト、Python確認、静的／Electronビルド。
- 画面・API・実行境界の変更では`pnpm test:e2e`、Electron・Python起動の変更では`pnpm test:desktop`も実行する。
- 同梱内容を変えたら`pnpm package:mac`後、READMEの手順でパッケージ済みアプリも確認する。
- テストの設計と利用者データの保護は[testsの規約](./tests/RULES.md)に従う。
- GitHubへのpush、公開リリース、署名・公証は通常のローカル開発の完了条件に含めない。
