# 図のガイド

## 設計内容と表示設定

- 図のノードと接続の意味はbase.jsonを正本とする。表示を補助するview.jsonは任意で、base.jsonだけでも図は表示できる。
- 最初にRULES.mdの対応表からbase.schema.jsonを読み、許可された項目・型・制約を確認する。
- ノードの役割はlabel・descriptionと文書で説明し、色・座標・大きさだけに意味を持たせない。
- 上位の図はその階層の部品と関係を描く。詳細はリンク先の文書や子の図へ分ける。
- 図を横型・縦型のフローに固定しない。処理の流れ、依存、構成など、説明する関係を先に決める。配置を調整するときは、その関係が読み取りやすい向きを選ぶ。接続の意味はsource・targetとラベルで示し、画面上の上下左右とは分ける。
- ノード・接続のIDは一意で安定したものにし、名前や配置の変更だけで振り直さない。**proto**・constructor・prototypeは使わない。
- 接続のsource・targetには、同じbase.jsonに存在するノードIDを指定する。構造変更後は重複・参照切れを確認する。

## base.jsonの例

執筆ガイドのMDXに対応する_flow/base.jsonの例です。

```json
{
  "version": 1,
  "nodes": [
    {
      "id": "input",
      "label": "input",
      "description": "入力を受け取る",
      "href": "../index.mdx"
    },
    {
      "id": "processor",
      "label": "processor",
      "description": "入力を処理する"
    }
  ],
  "edges": [
    {
      "id": "process",
      "source": "input",
      "target": "processor",
      "label": "入力を渡す"
    }
  ]
}
```

ノードのhrefはbase.jsonから文書への相対パスにする。接続の向きはbaseのsourceからtargetで表す。

## view.jsonの扱い

通常の文書・図の作成ではview.jsonを新設・変更しない。配置の調整はブラウザで行う。既存のview.jsonを削除せず、人間が保存した座標・サイズ・配色などを自動で丸めたり再配置したりしない。

表示設定の変更を明示的に依頼された場合はview.schema.jsonも読む。ノードや接続のIDはbase.jsonと対応させ、表示だけの変更でbaseの接続関係を変えない。図の見た目だけの設定はviewへ置く。

Schemaへの適合だけではノード・接続のIDの一意性や参照先の存在は保証されない。これらは作成時に確認し、アプリで読み込む際の検証にも従う。
