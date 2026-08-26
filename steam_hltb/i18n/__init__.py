from . import en, pt_br

LANGUAGES: tuple[str, ...] = ("en", "pt-BR")

_CATALOGS: dict[str, dict[str, str]] = {"en": en.MESSAGES, "pt-BR": pt_br.MESSAGES}
_active: str = "en"


def set_language(lang: str) -> None:
    global _active
    if lang not in _CATALOGS:
        raise ValueError(f"unsupported language: {lang}")
    _active = lang


def current_language() -> str:
    return _active


def t(key: str, **kwargs: object) -> str:
    message = _CATALOGS[_active][key]
    return message.format(**kwargs) if kwargs else message
