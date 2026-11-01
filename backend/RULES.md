# backend

このファイルはDjangoの業務処理・依存方向と固有の検査設定の正本とする。共通の実装原則・完了条件は[ルートの規約](../RULES.md)に従う。

Python 3.13、Django 5.2 LTS、DRF＋drf-spectacular。uvで依存を管理し、Ruff、mypy＋Django/DRF stubs、pytestを使う。

## Djangoが担当する範囲

一般利用者向けの画面はNext.jsが担当する。DjangoはAPI・Django Admin・業務処理・永続化を担当し、Djangoで生成する画面は管理者向けのAdminとAPI開発者向けのSwagger UI／ReDocに限る。

- 一般画面用のDjango View・Form・Templateは追加しない。Adminのカスタマイズに必要なForm・TemplateはAdmin側の責務として扱う。
- Next.jsの静的出力をbackendから配信する構成は維持する。静的ファイルの配信と、Djangoで画面を生成することを区別する。

## 配置と依存

アプリの実装は`src/`以下。`manage.py`とPyInstaller設定はbackend直下、テストは`tests/`に置く。環境と検査設定の配置は[共通規約の開発環境の配置](../RULES.md#開発環境の配置)に従う。

| 場所                | 担当                                               |
| ------------------- | -------------------------------------------------- |
| `src/config/`       | Django設定とURLの組み立て                          |
| `src/apps/<機能>/`  | Django app。モデル・migration・業務処理・Admin設定 |
| `src/apps/_common/` | 抽象モデルなど、機能app間で共有するDjango向け部品  |
| `src/api/`          | DRFのviews・serializers・URL・認証・権限処理       |
| `src/lib/`          | ファイル操作・外部通信の実装。業務ルールを持たない |
| `src/utils/`        | 外部I/O・共有状態を持たない小さな汎用関数          |
| `src/server.py`     | Web／デスクトップ共通の配信と起動・終了            |

- APIと業務処理を別の場所へ重複実装しない。機能固有の業務ルールはapps、ファイル・通信の実装はlib、機能に依存しない純粋な補助処理はutilsへ置く。
- 依存は`api → apps → lib → utils`を基本にする。apiはutilsも利用でき、appsはlibとutils、libは同じ層とutilsを利用できる。app間の依存は後述のbridgesとactionsを通す。逆向きの依存を作らない。configとserverは起動時の組み立てを担当する。
- 各機能appは`apps/_common/`を利用できる。`_common`から個別機能appへ依存させない。共通のファイル操作・外部通信・文字列処理は`_common`へ集めず、appsと同列のlib・utilsへ置く。
- `src/`がPythonのimport起点。mypyも`mypy_path`と`explicit_package_bases`で同じ起点を指定し、namespace packageを検査する。`apps.hello`、`api.views.greeting`等を使い、importに`backend.src`や`src`を付けない。apiはHTTP入口のパッケージであり、Django appとして登録しない。
- 実例は`apps/hello`の挨拶APIと`apps/notes`のSQLiteモデル・Django Admin。単純なAdmin保存に転送だけのserviceを追加しない。

## Pythonファイルを追加・削除するとき

通常のディレクトリには`__init__.py`を作らない。既知の例外は次の3つ。

- `apps/<機能>/models/__init__.py`：分割モデルを明示的にimportし、Djangoに登録する。ワイルドカードimportは使わない。
- `apps/<機能>/migrations/__init__.py`：Djangoのmigration検出に必要。生成・検出形式を維持する。
- `apps/__init__.py`：PyInstallerのDjango hookが`apps.__file__`を参照するため必要。

その他の例外は、実際の必要性を確認した場合だけ追加し、理由と確認結果を記す。空のパッケージ宣言や転送だけの再exportは追加しない。actions・services・bridges・adminsの関数やクラスは定義元から直接importする。削除時はimport・型チェック・同梱ビルドを確認する。

## 処理の責務

| 要素              | 担当すること                                                   |
| ----------------- | -------------------------------------------------------------- |
| DRF View          | HTTPの受付、Action・Service・モデルの呼び出し、応答への変換    |
| Serializer        | APIの入出力形式と入力検証                                      |
| Django Admin      | 管理者向けの表示・入力・操作と、その権限確認                   |
| Action            | 業務操作の公開入口、処理順序・実行条件・全体のトランザクション |
| Service           | 自app内の個別の業務処理。ファイル取込・モデルの更新など        |
| Bridge            | 他appのAction呼び出しと、連携に必要な引数・結果の変換          |
| Model             | 一件のデータ自身の制約・振る舞い・状態変更                     |
| QuerySet／Manager | 再利用する検索条件や、データの集合としての操作                 |

- サービスに置くかは、操作するモデルの数ではなく業務手順の有無で判断する。一つのモデルだけを扱うインポートもサービスの責務になる。
- モデル自身の制約や振る舞いを、サービスの採用を理由にすべてサービスへ移さない。単純な検索・登録は標準Managerを使い、再利用する検索条件が必要になったらQuerySet／Managerへまとめる。
- API・Admin・CLIで共通する業務操作は同じActionを呼び出す。個別の処理は同じServiceやモデルを使い、入口ごとに業務ルールを実装し直さない。
- CLIが必要になった場合はmanagement commandを入口にし、引数の受付と結果の出力を担当させる。業務処理はActionまたは単独のServiceへ渡し、必要になる前にcommandを追加しない。

## 入力検証とデータの制約

| 検証する内容                             | 定義・実行する場所                          |
| ---------------------------------------- | ------------------------------------------- |
| HTTP入力の形式・必須項目                 | APIのSerializer                             |
| Adminの入力形式                          | AdminのForm／ModelForm                      |
| ファイルの構造・項目・型                 | Importerなど、その入力を受け取るサービス    |
| 入口によらず成立すべきモデル自身の制約   | Modelのフィールド・validator・`clean()`など |
| 一意性や整合性のうちDBで保証できる条件   | Modelで定義するDB制約とmigration            |
| 複数データや現在の状態に依存する業務条件 | サービス。モデル自身の状態変更条件はModel   |

- SerializerはAPI専用とし、Admin・Importer・モデル・サービスから再利用しない。共通の制約はModelやサービスに定義し、各入口から適用する。
- `save()`は`full_clean()`を自動実行しない。モデルに検証を定義しただけで適用済みと考えず、API・Admin・Importerの各保存経路で必要な検証が実行されることを確認する。一括更新・一括登録でも検証を省略しない。
- 認証と入口固有の権限確認はAPI・Adminで行う。非公開データの所有者制限や入口に依存しない操作条件は、共通の検索・モデル・サービスでも適用し、別の入口から呼んでも抜けないようにする。HTTPのRequestをモデルやサービスへ渡さず、必要な利用者・対象・条件を明示的に渡す。

## トランザクションと副作用

- 保存にはDjango ORMとmigrationを使う。Serviceで、一件ごとか一括処理全体かという成功・失敗の単位を決める。複数のServiceやBridgeをまとめる場合は、Actionで操作全体の単位を決める。Bridgeで他appを呼ぶだけでトランザクションが分離されるわけではない。
- 競合による上書きや重複を防ぐ必要がある処理は、DB制約・条件付き更新・対応するDBのロックなど、保存方式に合った保護を行う。ファイル更新は排他制御や一時ファイルからの置換で元データを保護する。
- DBのロールバックで、ファイル変更や外部APIへの送信は取り消せない。DB確定後に行う通知などは`transaction.on_commit()`を検討する。確定後の処理に失敗してもDBは戻らないため、失敗の通知方法と再実行方法を決める。
- `save()`のオーバーライドやsignalsに、複数モデルの更新・外部通信などの業務手順を隠さない。サービスから明示的に呼び出す。signalsを使う場合は、直接呼び出せない理由と副作用を明記する。

## Django app内の配置

`src/apps/<機能>/`配下は、次の分類に揃える。必要なディレクトリだけを作り、処理の置き先を増やす目的で独自の分類を追加しない。

| ディレクトリ  | 置くもの                                                              |
| ------------- | --------------------------------------------------------------------- |
| `models/`     | ORMモデル、モデル自身の制約・validator、対象モデルのQuerySet／Manager |
| `admins/`     | ModelAdmin、Admin専用のForm／ModelForm、表示・管理操作の設定          |
| `actions/`    | 業務操作の公開入口。Service・Bridgeの組み立てと全体の実行管理         |
| `services/`   | 自appのモデルを使う個別の業務処理                                     |
| `bridges/`    | 他appの公開Actionを使う連携処理。呼び出し元のappに置く                |
| `migrations/` | Djangoのスキーマ移行・データ移行                                      |
| `utils/`      | 同じapp内の複数箇所で使う、外部I/Oのない純粋な補助関数                |

- QuerySet／Manager・validatorは、基本的に対象モデルと同じ`models/<モデル名>.py`に置く。QuerySet／Managerのコード量や責務が増えて見通しが悪くなった場合は、`models/querysets/`・`models/managers/`へ分割してよい。ファイル名は`<モデル名>.py`、用途別なら`<モデル名>_<用途名>.py`とし、クラス名にも対象と用途を表す。例：`models/querysets/note_published.py`の`PublishedNoteQuerySet`。同じ検索処理を両者に重複実装せず、QuerySetだけで足りる場合は`as_manager()`を使う。
- 分割したQuerySet／Managerはモデル側から定義元を直接importする。循環importを避け、型注釈だけのモデル参照は`TYPE_CHECKING`内、Managerから扱うモデルは`self.model`を使う。`models/__init__.py`は具体的なモデルの登録用とし、補助クラスの再exportを増やさない。
- Admin専用のFormは対象の`admins/<対象名>.py`に置く。app直下へ`managers/`・`validators/`・`forms/`などを独自に追加しない。
- app内の`utils/`は、その機能に固有の補助計算・解析・変換を担当する。DB・ファイル・ネットワーク・環境変数・共有状態にアクセスせず、モデル・サービス・API・configに依存しない。業務上の可否判定や状態変更はModel・サービスに置く。
- 一箇所でしか使わない補助処理は使用元のファイルに置く。app内で共用するものは`apps/<機能>/utils/<役割名>.py`、複数appで実際に共用する機能に依存しないものは`src/utils/<役割名>.py`に置く。`common.py`・`helpers.py`へ無関係な処理を集めない。
- `apps.py`・`admin.py`などDjangoが必要とする入口はapp直下に置く。management commandの`management/commands/`やAdmin専用の`templates/`・`static/`は、対応する機能が必要な場合に限って追加できる。
- 上記で分類できない責務が生じた場合は、既存の置き先で扱えない理由と依存方向を整理し、この規約・実例・関連チェックを更新してから分類を追加する。`repositories/`・`handlers/`などを実装ごとの判断で増やさない。

## Django向け共通部品：apps/_common

- `apps/_common/`は、複数の機能appで実際に使うDjango向け部品の共通パッケージとする。現時点の置き先は`models/`とし、抽象BaseModelや共通QuerySet／Managerを置ける。
- 共通の抽象モデルは`models/<役割名>.py`に置き、`Meta.abstract = True`を指定する。QuerySet／Managerの分割は各機能appと同じルールに従う。
- 抽象部品だけの`_common`は`INSTALLED_APPS`へ登録せず、`apps.py`・`migrations/`・モデル登録用の`__init__.py`も追加しない。各機能appから定義元を直接importする。
- テーブルを持つモデルは担当する業務appへ置く。共通化する実体ができるまで、空のBaseModelやディレクトリを作らない。

## Djangoアプリを変更するとき

- 一つの業務領域を`src/apps/<機能>/`にまとめる。`apps.py`のAppConfig.nameは`apps.<機能>`、INSTALLED_APPSはその設定クラスを指定する。
- モデルは`models/<モデル名>.py`、個別の業務処理は`services/<サービスの種類>/<対象名>.py`、業務操作は`actions/<用途名>.py`、app間の連携は`bridges/<用途名>.py`、Django Adminの設定は`admins/<対象名>.py`に分ける。`models.py`・`services.py`・`actions.py`・`bridges.py`・`admins.py`に集約しない。ファイル名はsnake_case、内容と責務が分かる名前にする。
- servicesを汎用コード置き場にしない。業務上の判断・モデル操作はapp内に置き、ファイル読書き・外部通信はlibの処理を呼び出す。
- `admins/`はModelAdmin、表示・検索・フィルター・管理操作のUIを担当する。管理操作の業務手順はActionまたは単独のServiceへ渡し、API側と重複実装しない。
- Djangoは`admin`モジュールを自動検出するため、Adminを使うappには薄い`admin.py`を置く。そこではmodels・adminsから必要なクラスを明示的にimportし、`admin.site.register`で登録する。ModelAdmin本体や業務処理は書かない。独自の自動探索は作らない。
- models・actions・services・bridgesにHTTPのRequest・ResponseやDRF Serializerを持ち込まない。REST APIのviews・serializers・URLは`src/api/`へ置く。adminsではDjango Adminが要求するHttpRequest等は利用できる。appからapiやconfigをimportしない。
- 配置変更だけで既存のAppConfig.labelやmigrationの参照を変えない。

Admin登録とモデル読み込みはDjangoチェック・テストでも確認する。必要のない機能ディレクトリや、転送だけのserviceは作らない。

参考：[モデルのパッケージ分割](https://docs.djangoproject.com/en/5.2/topics/db/models/#organizing-models-in-a-package)、[Adminの自動検出](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#discovery-of-admin-files)。

## 業務操作とapp間の境界：actions・services・bridges

業務領域ごとにappを分け、同じDjango内で動かすモジュラーモノリスとして扱う。Actionは操作を提供する側の入口、Bridgeはその操作を利用する側の連携窓口である。

- `actions/<用途名>.py`に、業務操作の公開入口となるクラスを置く。自appのService・Bridgeを明示的にimportし、実行順序・条件分岐・結果の集約・全体のトランザクションを管理する。対象ごとの処理はServiceへ置く。例：`apps/notes/actions/importer.py`の`Importer`が`NoteImporter`を呼ぶ。
- Actionは用途ごとに複数定義してよい。ファイル名は処理の目的が分かるsnake_case、クラス名は対応するPascalCaseとする。例：`importer_initial.py`の`ImporterInitial`。複数処理をまとめる場合に加え、他appへ公開する必要があれば、単独のServiceを呼ぶActionも作ってよい。
- `bridges/<用途名>.py`に、他appの公開Actionを呼ぶクラスを置く。ファイル名・クラス名はActionと同じ命名規則とする。呼び出し元の条件を相手の引数へ変換し、結果を呼び出し元で使える形へ整える。相手appの業務ルールを実装し直さない。
- app間の呼び出しは`自appのAction → 自appのBridge → 相手appのAction`を基本とする。他appのモデル・QuerySet・Manager・Serviceを直接importして参照・更新しない。必要な検索や更新は相手appのActionとして提供する。戻り値やORMの関連を経由してこの境界を迂回しない。共通部品の`apps/_common/`はこの制限の対象外とする。
- ServiceからAction・Bridgeへ依存させず、Bridgeから自appのAction・Serviceへ依存させない。連携の前後に必要な自appの処理はActionが組み立てる。app間の循環依存も作らない。
- 同じapp内の利用やAPI・Admin・CLIからの単独処理では、Serviceを直接呼んでよい。単純なCRUDにActionを必須にしない。他appから使う場合は必ずBridgeと公開Actionを通す。
- Bridgeは同じDjango内のapp連携を担当する。外部サービスとのHTTP通信・ファイル操作の実装は`src/lib/`へ置く。実際にapp間の連携が必要になるまで、空のbridgesディレクトリやダミークラスは作らない。

## サービスクラス（Service Object）の共通の書き方

Action・Service・Bridgeはいずれも、`__init__`と`run()`を基本とするクラスで書く。以下の実行条件・結果・失敗・再実行の規則を共通で適用する。

- 一つのファイルに、その処理を代表するクラスを一つ置く。個別のServiceは`src/apps/<機能>/services/<サービスの種類>/<対象名>.py`に置く。ディレクトリ名は`importers`・`exporters`など役割を表す複数形、ファイル名は対象を表すsnake_case、クラス名は対象と役割を組み合わせたPascalCaseにする。例：`apps/notes/services/importers/note.py`の`NoteImporter`。処理の組み立てを`services/`直下へ置かず、`actions/`へ置く。
- `__init__`で対象ディレクトリや処理設定などの実行条件を受け取り、インスタンス属性として保持する。複数メソッドで使う実行条件は、引数で繰り返し渡さず属性を積極的に使う。実行中だけ使う一時データはローカル変数にする。
- 複数の処理結果を公開する場合は`self.results`を使う。`__init__`で型を付けて空のリストとして定義し、`run()`の冒頭で新しい空のリストに初期化する。前回の結果を次の実行へ持ち越さず、処理が成功してから今回の結果を格納する。同じインスタンスを同時実行しない。
- `__init__`では実行条件の保持と検証を行い、ファイルの読み書き・DB操作・外部通信は行わない。公開する実行入口は`run()`に統一し、処理結果を戻り値で返す。引数と戻り値には型注釈を付ける。
- `run()`は上から読める業務手順として書く。必要な場合だけ非公開メソッドへ分け、入力検証・権限確認・トランザクション・失敗時のデータ保護・後始末を省略しない。
- 処理の失敗は例外として呼び出し側へ伝える。失敗を握りつぶして、成功件数・`0`・`None`などの通常の戻り値に変換しない。例外を変換する場合は元の原因を保持する。
- 同じ入力で再実行した場合の扱いを`run()`のdocstringや機能の仕様に明記する。追加・更新・スキップ・拒否など、重複データの扱いと、失敗後に途中までの変更が残るかを明確にする。再実行できることや、重複しないことを暗黙の前提にしない。
- 標準Managerへ転送するだけのserviceや、要求されていない汎用基底クラスは作らない。サービスの種類ごとのディレクトリは、実際の処理が必要になった時点で追加する。

## 業務フローを図示するとき

Actionの追加や、処理順・条件分岐・呼び出し先・失敗時の挙動を変更した場合は、対応する設計文書と図を作成・更新する。図の単位・描き方・コードとの照合は[設計ドキュメントの図示規約](../docs/RULES.md#業務処理の図示)に従う。

## HTTP APIを変更するとき

- viewは`api/views/<APIの内容>.py`、serializerは`api/serializers/<APIの内容>.py`に置く。例：`views/greeting.py`と`serializers/greeting.py`。APIの内容が分かる名前を使い、`views.py`・`serializers.py`一つに集約しない。
- URLはapi直下の`urls.py`、Django側の接続は`config/urls.py`で組み立てる。クラスは`api.views.greeting`等の定義元から直接importする。views・serializers内に、空の`__init__.py`や再exportだけのファイルを追加しない。ツール上必要になった場合は理由と確認結果を残す。
- Django appごとのディレクトリは作らず、appsとの1対1対応を強制しない。HTTPの責務に応じて分け、アプリの増加だけを理由に階層を増やさない。
- viewsはHTTPの受付と応答、serializersは入出力の検証。生の入力を業務処理へ渡さない。共通の認証・権限処理はapi直下に置く。
- REST APIはDRFを標準とし、Serializer・ViewSet・Routerを可能な限り利用する。ViewSetは`api/views/`、Routerの登録は`api/urls.py`に置く。固定応答などリソース操作でないAPIにはAPIViewと明示したURLを使う。認証・権限・ページング・フィルタリング・Request／Response検証にはDRFの標準機能を優先する。
- APIを提供するDjangoテンプレートにはdrf-spectacularを標準採用し、コードからOpenAPI 3.xを生成する。Serializer・ViewSetから推論できない応答・query/path parameter・認証方式だけを`extend_schema`や認証拡張で補う。Permissionによるアクセス制限と認証方式を混同しない。
- OpenAPIをfrontend・AIエージェントとの機械可読な契約とする。コード → OpenAPI → 人間向け文書／クライアント／AIの一方向で生成し、README・Wiki・手書き仕様書に個々のAPI仕様を重複管理しない。設定・生成手順は[API設計文書](../docs/django/api/index.mdx)を参照する。
- 単純な固定応答はviewに直接書いてよい。業務手順の組み立てはappsのActionへ渡し、単独のServiceで足りる場合は直接呼んでよい。単純な一覧・作成はモデルの標準Managerを直接使ってよい。モデル・migration・業務ルールをapiへ置かない。
- view/serializerからOS操作・外部HTTPを直接呼ばない。libの外部連携もappsの処理を通して利用する。
- API契約の変更はSerializer、呼び出し側の検証、契約テストを一緒に更新する。frontend/native双方が使う契約はshared、Web専用のNote契約はfrontendのutils/typesに置く。

## 外部I/O：src/lib

| 配置                        | 担当                                          |
| --------------------------- | --------------------------------------------- |
| `lib/files/<役割名>.py`     | ファイルの読込・書込。例：`json.py`のJSON読込 |
| `lib/clients/<接続先名>.py` | 外部API・外部サービスへの通信                 |

- API・モデル・Action・Service・Bridgeはファイル・ネットワークへ直接アクセスしない。Serviceからlibを呼び出し、入出力されたデータの業務上の検証・モデルへの登録を行う。DB操作はDjango ORMを使い、libへ移さない。設定読込・サーバー起動・migration・Django標準のAdminや静的配信は、それぞれの実行境界で扱う。
- libはファイル形式や通信プロトコルを扱い、特定モデルの項目・業務ルールを持たない。機能固有のパス・URL・設定は呼び出し側から渡す。利用箇所が一つでも、ファイル・通信の実装はこの配置に揃える。
- APIのRequest・Responseに依存せず、普通の引数と戻り値を使う。apps・api・configをimportしない。utilsは利用できる。
- 外部I/Oには入力検証・タイムアウト・エラー・後始末を定義する。副作用をimport時に実行しない。
- 利用者データの読み書きでは保存先制限と失敗時のデータ保護を維持する。実際の処理が必要になるまで、空のディレクトリ・ダミーのクライアント・汎用基底クラスは作らない。

## src/utilsに純粋な関数を置くとき

- 外部I/O・共有状態を持たず、引数から結果を返す小さな汎用関数だけを置く。機能固有の計算はappsに残す。
- ファイル・ネットワーク・環境変数・DBへアクセスしない。Django・DRF・apps・api・lib・configに依存しない。
- `common.py`や`helpers.py`へ無関係な処理を集めず、役割が分かるモジュール名にする。数行の処理を機械的に切り出さない。

## 共通の実装規約

- パス・ポート・プロセス管理は起動境界に置く。利用者データをアプリのインストール先に書かない。
- 例外を成功レスポンスに変えない。認証・権限・所有者の確認を省略しない。デスクトップのトークンは利用者認証ではない。
- 挨拶APIと公開サンプルのNote APIは認証不要。Noteは既存分を含め全員共通で閲覧・追加でき、投稿には入力検証とCSRF保護を適用する。Adminの編集・削除はログインとモデル権限が必要。今後、非公開の利用者データを追加する場合は認証と所有者制限を実装する。
- testsを除くアプリコードは型注釈を付ける。ライブラリに型がない箇所は境界だけに限定する。

`src/server.py`はWaitressでAPIとNext静的出力を同一originから配信する。デスクトップ起動ではloopback＋ランダムport＋起動ごとのtoken、stdin EOFで終了。開発用`runserver`を配布物には使わない。

## 完了確認

個別の確認はルートから`pnpm typecheck:backend`・`pnpm test:backend`。`mypy.ini`でDjango/DRFプラグイン、`pytest.ini`でDjango設定を指定する。プロセス・import起点の分離とPython全体の確認は[開発環境の配置](../RULES.md#開発環境の配置)、テスト設計・保護は[testsの規約](../tests/RULES.md)に従う。新しいDjango app・APIを追加したらDjangoの登録・URLとPyInstallerのhiddenimportsも更新する。ASTチェックはsrc配下を再帰的に検査する。PY01–02は実行境界、PY03はソース・app・APIの配置と旧来の単一ファイル配置の禁止、PY04は内部の依存方向を確認する。間接呼び出しの副作用、責務の妥当性、`__init__.py`の必要性はレビューする。

PY02では既知のI/Oモジュールのimportと`open`・`read_text`等の直接呼出し、PY03ではapp内とlibの分類、PY04ではapp間のBridge → Actionのimport、Service・Bridgeから自appへの逆依存、`_common`から個別appへの依存、utilsの独立性も確認する。動的import・ORMの関連を介したアクセス・app間の循環・すべてのI/Oを検出するものではなく、これらはレビューで確認する。
