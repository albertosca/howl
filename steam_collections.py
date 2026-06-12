import os
import re

DEFAULT_VDF_PATH = "sharedconfig.vdf"


def load_collections(vdf_path: str = DEFAULT_VDF_PATH) -> dict:
    """Retorna {appid_str: [collection_names]} lido do sharedconfig.vdf."""
    if not os.path.exists(vdf_path):
        return {}
    with open(vdf_path, "r", encoding="utf-8") as f:
        content = f.read()
    result = {}
    app_blocks = re.findall(
        r'"(\d+)"\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}',
        content,
        re.DOTALL,
    )
    for appid, block in app_blocks:
        tag_match = re.search(r'"tags"\s*\{([^}]*)\}', block, re.DOTALL)
        if not tag_match:
            continue
        tags = re.findall(r'"\d+"\s*"([^"]+)"', tag_match.group(1))
        if tags:
            result[appid] = tags
    return result


def filter_collection(games: list, collection: str, collection_map: dict) -> list:
    col_lower = collection.lower()
    return [
        g for g in games
        if col_lower in [c.lower() for c in collection_map.get(str(g.get("appid", "")), [])]
    ]
