import sys
import pytest


def _parse(argv):
    sys.argv = ["main.py"] + argv
    from main import parse_args
    return parse_args()


def test_parse_args_defaults():
    args = _parse([])
    assert args.top == 10
    assert args.sort == "hltb_short"
    assert args.verbose is False
    assert args.show_tags is False


def test_parse_args_verbose_short():
    args = _parse(["-v"])
    assert args.verbose is True


def test_parse_args_show_tags():
    args = _parse(["--show-tags"])
    assert args.show_tags is True


def test_parse_args_top():
    args = _parse(["--top", "25"])
    assert args.top == 25
