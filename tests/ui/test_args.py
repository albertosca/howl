import sys


def _parse(argv):
    sys.argv = ["main.py", *argv]
    from steam_hltb.ui.args import parse_args

    return parse_args()


def test_parse_args_defaults():
    args = _parse([])
    assert args.top == 10
    assert args.sort == "shortest"
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


def test_parse_args_list_tags():
    args = _parse(["--list-tags"])
    assert args.list_tags is True


def test_parse_args_list_genres():
    args = _parse(["--list-genres"])
    assert args.list_genres is True


def test_parse_args_list_collections():
    args = _parse(["--list-collections"])
    assert args.list_collections is True


def test_parse_args_era_flag():
    args = _parse(["--era", "2010-2015,2020+"])
    assert args.era == "2010-2015,2020+"


def test_parse_args_era_not_set_by_default():
    args = _parse([])
    assert getattr(args, "era", None) is None


def test_parse_args_show_finished():
    args = _parse(["--show-finished"])
    assert args.show_finished is True


def test_progress_mode_all():
    import argparse

    args = argparse.Namespace(not_started=False, in_progress=False, all_progress=True)
    from steam_hltb.ui.args import _progress_mode

    assert _progress_mode(args) == "all"


def test_progress_mode_not_started():
    import argparse

    args = argparse.Namespace(not_started=True, in_progress=False, all_progress=False)
    from steam_hltb.ui.args import _progress_mode

    assert _progress_mode(args) == "not_started"


def test_progress_mode_default_when_nothing_set():
    import argparse

    args = argparse.Namespace(not_started=False, in_progress=False, all_progress=False)
    from steam_hltb.ui.args import _progress_mode

    assert _progress_mode(args) == "default"


def test_progress_mode_in_progress():
    import argparse

    from steam_hltb.ui.args import _progress_mode

    args = argparse.Namespace(not_started=False, in_progress=True, all_progress=False)
    assert _progress_mode(args) == "in_progress"


def test_weights_normalization_warns_and_normalizes(capsys):
    import argparse

    args = argparse.Namespace(weight_mc=0.6, weight_steam=0.6)
    from steam_hltb.ui.args import _weights

    w = _weights(args)
    err = capsys.readouterr().err
    assert "Aviso" in err
    assert abs(sum(w.values()) - 1.0) < 0.01


def test_csv_list_parses_comma_separated():
    from steam_hltb.ui.args import _csv_list

    assert _csv_list("action,rpg") == ["action", "rpg"]
    assert _csv_list("action, rpg , puzzle") == ["action", "rpg", "puzzle"]


def test_csv_list_returns_none_for_empty():
    from steam_hltb.ui.args import _csv_list

    assert _csv_list(None) is None
    assert _csv_list("") is None
    assert _csv_list("  ") is None


def test_resolve_username_prompts_when_missing(monkeypatch):
    import argparse

    from steam_hltb.ui.args import _resolve_username

    args = argparse.Namespace(username=None)
    monkeypatch.setattr("builtins.input", lambda _: "  alice  ")
    assert _resolve_username(args) == "alice"


def test_resolve_username_exits_when_empty(monkeypatch):
    import argparse

    import pytest

    from steam_hltb.ui.args import _resolve_username

    args = argparse.Namespace(username=None)
    monkeypatch.setattr("builtins.input", lambda _: "")
    with pytest.raises(SystemExit):
        _resolve_username(args)
