import { isBuiltin } from "node:module";
import { dirname, resolve, sep } from "node:path";

const architecture = {
  rules: {
    boundaries: {
      meta: {
        type: "problem",
        schema: [],
        messages: { boundary: "{{reason}}" },
      },
      create(context) {
        const filename = context.filename.split(sep).join("/");
        const frontend = filename.includes("/frontend/");
        const shared = filename.includes("/shared/");
        const srcPath = filename.split("/frontend/src/")[1];
        const layer = srcPath?.split("/")[0];
        const runtime = filename.endsWith("/frontend/src/utils/runtime.ts");
        const page = layer === "app" && /\/page\.tsx$/.test(filename);
        let pageName;
        const dependencies = {
          app: ["app", "layout", "components", "types"],
          layout: [
            "layout",
            "components",
            "hooks",
            "types",
            "my-ui",
            "ui",
            "utils",
          ],
          components: ["components", "hooks", "types", "my-ui", "ui", "utils"],
          hooks: ["hooks", "types", "utils"],
          utils: ["utils", "types"],
          types: ["types"],
          "my-ui": ["my-ui", "ui", "types", "utils", "hooks"],
          ui: ["ui", "types", "utils", "hooks"],
        };
        const report = (node, reason) =>
          context.report({ node, messageId: "boundary", data: { reason } });
        const typeOnly = (node) =>
          node.importKind === "type" ||
          node.exportKind === "type" ||
          (node.specifiers?.length > 0 &&
            node.specifiers.every(
              (specifier) => specifier.importKind === "type",
            ));
        function checkImport(node, source) {
          if (typeof source !== "string") {
            report(node, "ARCH01: 動的なimport先は禁止。依存先を明示する。");
            return;
          }
          if (layer === "utils" && source === "react") {
            report(
              node,
              "FE03: utilsはReactに依存しない。Reactの処理はhooksへ置く。",
            );
          }
          if (
            frontend &&
            (isBuiltin(source) ||
              [
                "electron",
                "server-only",
                "next/headers",
                "next/server",
              ].includes(source))
          ) {
            report(
              node,
              "ARCH01: frontendからNode/Electron/Nextサーバー機能を呼ばない。",
            );
          }
          if (
            layer &&
            source.endsWith(".css") &&
            !(srcPath === "app/layout.tsx" && source === "./globals.css")
          ) {
            report(
              node,
              "FE01: CSSはapp/layout.tsxからglobals.cssだけを読み込み、部品はTailwindで装飾する。",
            );
          }
          if (
            layer &&
            source === "@tanstack/react-query" &&
            !["hooks", "layout", "types"].includes(layer)
          ) {
            report(
              node,
              "FE02: TanStack QueryはhooksとlayoutのProviderで使う。",
            );
          }
          if (source.startsWith(".") || source.startsWith("@/")) {
            const frontendRoot =
              filename.split("/frontend/")[0] + "/frontend/src/";
            const target = (
              source.startsWith("@/")
                ? resolve(frontendRoot, source.slice(2))
                : resolve(dirname(filename), source)
            )
              .split(sep)
              .join("/");
            const targetPath = target.startsWith(frontendRoot)
              ? target.slice(frontendRoot.length)
              : undefined;
            const targetLayer = targetPath?.split("/")[0];
            if (layer && targetLayer && layer !== "ui") {
              const sameDirectory = dirname(filename) === dirname(target);
              if (
                !(sameDirectory
                  ? source.startsWith("./")
                  : source.startsWith("@/"))
              )
                report(
                  node,
                  "FE14: src内の別ディレクトリは@/、同じディレクトリは./でimportする。",
                );
            }
            if (
              layer &&
              targetLayer &&
              !dependencies[layer]?.includes(targetLayer) &&
              !(layer === "types" && targetLayer === "utils" && typeOnly(node))
            ) {
              report(node, `FE03: ${layer}から${targetLayer}への依存は禁止。`);
            }
            if (
              layer &&
              targetPath?.replace(/\.[cm]?[jt]sx?$/, "") === "utils/runtime" &&
              layer !== "hooks" &&
              !runtime
            ) {
              report(
                node,
                "FE04: 画面から通信処理を直接呼ばず、hooksを経由する。",
              );
            }
            if (layer === "components" && targetLayer === "components") {
              const ownGroup = srcPath.split("/");
              const targetGroup = targetPath.split("/");
              if (
                ownGroup.length > 2 &&
                targetGroup.length > 2 &&
                ownGroup[1] !== targetGroup[1]
              ) {
                report(
                  node,
                  "FE05: 別機能のcomponentsを直接importしない。組み合わせはapp/layoutで行う。",
                );
              }
            }
            if (frontend && /\/(backend|native)\//.test(target))
              report(
                node,
                "ARCH02: frontendはbackend/nativeの実装をimportしない。",
              );
            if (
              filename.includes("/native/src/") &&
              /\/(backend|frontend)\//.test(target)
            )
              report(
                node,
                "ARCH02: nativeはbackend/frontendの実装をimportしない。",
              );
            if (shared && !target.includes("/shared/"))
              report(node, "ARCH02: sharedはアプリの実装に依存しない。");
          } else if (shared) {
            report(node, "ARCH02: sharedは外部パッケージに依存しない。");
          }
        }
        function checkType(node) {
          if (layer && !["types", "ui"].includes(layer))
            report(
              node,
              "FE06: 独自の型・Props型はsrc/typesに置く。shadcn取得コードは例外。",
            );
        }
        function checkHook(node, name) {
          if (
            layer &&
            /^use[A-Z]/.test(name ?? "") &&
            !["hooks", "ui"].includes(layer)
          )
            report(node, "FE07: 独自hookの定義はsrc/hooksに置く。");
        }
        function checkPageComponent(node, name) {
          if (page && /^[A-Z]/.test(name ?? "") && name !== pageName)
            report(
              node,
              "FE13: pageは組立だけ。追加のコンポーネントはsrc/componentsに役割が分かる名前で定義する。",
            );
        }
        return {
          Program(node) {
            const defaultExport = node.body.find(
              (item) => item.type === "ExportDefaultDeclaration",
            )?.declaration;
            pageName = defaultExport?.id?.name ?? defaultExport?.name;
            if (
              frontend &&
              !srcPath &&
              !filename.endsWith("/frontend/next.config.ts")
            )
              report(node, "FE08: アプリのソースはfrontend/src以下に置く。");
            if (layer && !(layer in dependencies))
              report(
                node,
                "FE08: src直下はapp/layout/components/types/hooks/utils/ui/my-uiに揃える。",
              );
            if (
              srcPath &&
              !/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*(?:\.d)?\.[jt]sx?$/.test(
                srcPath.split("/").at(-1),
              )
            )
              report(node, "FE09: ソースのファイル名はkebab-caseにする。");
            if (
              frontend &&
              (/\/(route|middleware|proxy)\.[cm]?[jt]sx?$/.test(filename) ||
                filename.includes("/src/app/api/"))
            )
              report(node, "ARCH03: Next.jsのサーバーエンドポイントは禁止。");
          },
          ImportDeclaration(node) {
            checkImport(node, node.source.value);
            if (layer === "types" && !typeOnly(node))
              report(node, "FE10: types内はimport typeで依存する。");
          },
          ExportDefaultDeclaration(node) {
            if (layer && !["app", "ui"].includes(layer))
              report(
                node,
                "FE11: Next.js規定ファイル以外の独自コードはnamed exportにする。",
              );
          },
          ExportNamedDeclaration(node) {
            if (node.source) checkImport(node, node.source.value);
          },
          ExportAllDeclaration(node) {
            checkImport(node, node.source.value);
          },
          ImportExpression(node) {
            checkImport(node, node.source.value);
          },
          ExpressionStatement(node) {
            if (frontend && node.directive === "use server")
              report(node, "ARCH03: Server Actionsは禁止。");
            if (page && node.directive === "use client")
              report(
                node,
                "FE13: pageは組立だけ。操作する部品をcomponentsへ置く。",
              );
          },
          TSTypeAliasDeclaration: checkType,
          TSInterfaceDeclaration: checkType,
          TSTypeLiteral: checkType,
          TSEnumDeclaration(node) {
            if (layer === "types")
              report(
                node,
                "FE10: typesには実行時の値を作るenumではなく型を置く。",
              );
          },
          FunctionDeclaration(node) {
            checkHook(node, node.id?.name);
            checkPageComponent(node, node.id?.name);
            if (layer === "types")
              report(node, "FE10: typesに実行する処理を置かない。");
          },
          VariableDeclarator(node) {
            if (
              ["ArrowFunctionExpression", "FunctionExpression"].includes(
                node.init?.type,
              )
            ) {
              checkHook(node, node.id.name);
              checkPageComponent(node, node.id.name);
            }
            if (layer === "types")
              report(node, "FE10: typesに実行する値を置かない。");
          },
          JSXElement(node) {
            if (["hooks", "utils", "types"].includes(layer))
              report(node, "FE12: JSXはapp/layout/components/my-ui/uiに置く。");
          },
          JSXFragment(node) {
            if (["hooks", "utils", "types"].includes(layer))
              report(node, "FE12: JSXはapp/layout/components/my-ui/uiに置く。");
          },
          JSXAttribute(node) {
            if (page && /^on[A-Z]/.test(node.name.name ?? ""))
              report(
                node,
                "FE13: pageに操作イベントを書かずcomponentsへ置く。",
              );
          },
          CallExpression(node) {
            if (frontend && node.callee.name === "require")
              report(node, "ARCH01: frontendはES modulesを使う。");
            const name = node.callee.name ?? node.callee.property?.name;
            if (page && /^use[A-Z]/.test(name ?? ""))
              report(node, "FE13: pageでhooksを使わずcomponentsから利用する。");
          },
          Identifier(node) {
            if (
              frontend &&
              layer !== "types" &&
              !runtime &&
              [
                "fetch",
                "XMLHttpRequest",
                "WebSocket",
                "EventSource",
                "desktop",
              ].includes(node.name)
            )
              report(
                node,
                "ARCH04: 通信とdesktop bridgeへのアクセスはutils/runtime.tsに集める。",
              );
          },
          MemberExpression(node) {
            if (
              frontend &&
              !runtime &&
              node.computed &&
              ["fetch", "desktop"].includes(node.property.value)
            )
              report(
                node,
                "ARCH04: 通信とdesktop bridgeへのアクセスはutils/runtime.tsに集める。",
              );
          },
        };
      },
    },
  },
};

export default architecture;
