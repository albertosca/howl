import argparse
import ast
import pathlib

from steam_hltb.i18n import pt_br, set_language
from steam_hltb.i18n.argparse_hook import CORE_STRINGS, install


def _gettext_strings_in_running_argparse() -> set[str]:
    source = pathlib.Path(argparse.__file__).read_text(encoding="utf-8")
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = (
            func.id
            if isinstance(func, ast.Name)
            else func.attr
            if isinstance(func, ast.Attribute)
            else ""
        )
        if name in ("_", "gettext", "ngettext"):
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    found.add(arg.value)
    return found


def test_core_strings_still_exist_in_running_python():
    missing = set(CORE_STRINGS) - _gettext_strings_in_running_argparse()
    assert not missing, f"argparse reworded these on this Python: {sorted(missing)}"


def test_argparse_exposes_the_private_alias():
    assert hasattr(argparse, "_"), "argparse no longer has the gettext alias this hook patches"


def test_portuguese_catalog_covers_every_core_string():
    assert set(pt_br.ARGPARSE) == set(CORE_STRINGS)


def test_help_is_english_when_language_is_english(capsys):
    install()
    set_language("en")
    parser = argparse.ArgumentParser(prog="howl", add_help=True)
    parser.print_help()
    out = capsys.readouterr().out
    assert "usage:" in out
    assert "show this help message and exit" in out


def test_help_is_portuguese_when_language_is_portuguese(capsys):
    install()
    set_language("pt-BR")
    parser = argparse.ArgumentParser(prog="howl", add_help=True)
    parser.print_help()
    out = capsys.readouterr().out
    assert "uso:" in out
    assert "mostra esta ajuda e sai" in out
    assert "opções:" in out
