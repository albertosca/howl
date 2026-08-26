from collections.abc import Mapping

from . import LANGUAGES

_FLAG = "--lang"
_ENV_VAR = "HOWL_LANG"
_PT_BR_LOCALE_PREFIX = "pt_BR"
_DEFAULT = "en"


def _from_argv(argv: list[str]) -> str | None:
    for index, arg in enumerate(argv):
        if arg == _FLAG and index + 1 < len(argv):
            return argv[index + 1]
        if arg.startswith(f"{_FLAG}="):
            return arg.split("=", 1)[1]
    return None


def _from_locale(env: Mapping[str, str]) -> str | None:
    locale = env.get("LC_ALL") or env.get("LANG") or ""
    return "pt-BR" if locale.startswith(_PT_BR_LOCALE_PREFIX) else None


def resolve_language(argv: list[str], env: Mapping[str, str], env_file: Mapping[str, str]) -> str:
    """Precedence: --lang > HOWL_LANG > .env > OS locale > en."""
    for candidate in (
        _from_argv(argv),
        env.get(_ENV_VAR),
        env_file.get(_ENV_VAR),
        _from_locale(env),
    ):
        if candidate in LANGUAGES:
            return candidate
    return _DEFAULT
