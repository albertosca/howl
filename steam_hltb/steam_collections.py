import os
import re

DEFAULT_VDF_PATH = os.environ.get("STEAM_VDF_PATH", "sharedconfig.vdf")
FINISHED_COLLECTION = "Terminados"


def load_collections(vdf_path: str = DEFAULT_VDF_PATH) -> dict[str, list[str]]:
    """Retorna {appid_str: [collection_names]} lido do sharedconfig.vdf."""
    if not os.path.exists(vdf_path):
        return {}
    with open(vdf_path, "r", encoding="utf-8") as f:
        content = f.read()
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
    games: list[dict],
    collection: str,
    collection_map: dict[str, list[str]],
) -> list[dict]:
    col_lower = collection.lower()
    return [
        g for g in games
        if col_lower in [c.lower() for c in collection_map.get(str(g.get("appid", "")), [])]
    ]


def exclude_finished(
    games: list[dict],
    vdf_path: str = DEFAULT_VDF_PATH,
) -> list[dict]:
    """Remove games na coleção 'Terminados'. Silencioso se VDF não existir."""
    collection_map = load_collections(vdf_path)
    if not collection_map:
        return games
    finished_ids = {
        appid for appid, tags in collection_map.items()
        if FINISHED_COLLECTION in tags
    }
    return [g for g in games if str(g.get("appid", "")) not in finished_ids]
