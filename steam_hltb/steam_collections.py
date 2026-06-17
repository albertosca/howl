import os
import re
from pathlib import Path
from typing import Any

DEFAULT_VDF_PATH = os.environ.get("STEAM_VDF_PATH", "sharedconfig.vdf")
FINISHED_COLLECTION = "Terminados"


def load_collections(vdf_path: str = DEFAULT_VDF_PATH) -> dict[str, list[str]]:
    """Retorna {appid_str: [collection_names]} lido do sharedconfig.vdf."""
    path = Path(vdf_path)
    if not path.exists():
        return {}
    content = path.read_text(encoding="utf-8")
    result: dict[str, list[str]] = {}
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


def filter_collection(
    games: list[dict[str, Any]],
    collection: str,
    collection_map: dict[str, list[str]],
) -> list[dict[str, Any]]:
    col_lower = collection.lower()
    return [
        g
        for g in games
        if col_lower in [c.lower() for c in collection_map.get(str(g.get("appid", "")), [])]
    ]


def exclude_finished(
    games: list[dict[str, Any]],
    vdf_path: str = DEFAULT_VDF_PATH,
) -> list[dict[str, Any]]:
    """Remove games na coleção 'Terminados'. Silencioso se VDF não existir."""
    collection_map = load_collections(vdf_path)
    if not collection_map:
        return games
    finished_ids = {appid for appid, tags in collection_map.items() if FINISHED_COLLECTION in tags}
    return [g for g in games if str(g.get("appid", "")) not in finished_ids]
