import argparse

from . import current_language, pt_br

# Present in every argparse from CPython 3.11 through 3.14, measured on
# 2026-08-25 by parsing Lib/argparse.py from each branch. Strings outside
# this set differ between versions and stay untranslated on purpose.
CORE_STRINGS: tuple[str, ...] = (
    " (default: %(default)s)",
    "%(heading)s:",
    "%(prog)s: error: %(message)s\n",
    "ambiguous option: %(option)s could match %(matches)s",
    'argument "-" with mode %r',
    "argument %(argument_name)s: %(message)s",
    "can't open '%(filename)s': %(error)s",
    "conflicting option string: %s",
    "conflicting option strings: %s",
    "expected %s argument",
    "expected %s arguments",
    "expected at least one argument",
    "expected at most one argument",
    "expected one argument",
    "ignored explicit argument %r",
    "invalid %(type)s value: %(value)r",
    "invalid choice: %(value)r (choose from %(choices)s)",
    "not allowed with argument %s",
    "one of the arguments %s is required",
    "options",
    "positional arguments",
    "show program's version number and exit",
    "show this help message and exit",
    "the following arguments are required: %s",
    "unexpected option string: %s",
    "unknown parser %(parser_name)r (choices: %(choices)s)",
    "unrecognized arguments: %s",
    "usage: ",
)

_CATALOGS: dict[str, dict[str, str]] = {"pt-BR": pt_br.ARGPARSE}


def _translate(message: str) -> str:
    catalog = _CATALOGS.get(current_language())
    return catalog.get(message, message) if catalog else message


def install() -> None:
    """Patch argparse's gettext alias.

    `gettext.NullTranslations().install()` does not work here: argparse binds
    `from gettext import gettext as _` at import time, so a later install is
    never consulted. Rebinding the alias is the only mechanism that takes
    effect. Verified on 3.14.6; test_argparse_hook covers the boundary.
    """
    argparse._ = _translate  # type: ignore[attr-defined]
