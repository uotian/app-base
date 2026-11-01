import json
from pathlib import Path


def read_json(path: Path) -> object:
    """UTF-8のJSONを読み込む。読込・解析の失敗は呼び出し側へ伝える。"""
    return json.loads(path.read_text(encoding="utf-8"))
