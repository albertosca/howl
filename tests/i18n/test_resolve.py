from steam_hltb.i18n.resolve import resolve_language


def test_flag_wins_over_everything():
    lang = resolve_language(
        argv=["howl", "--lang", "pt-BR"],
        env={"HOWL_LANG": "en", "LANG": "en_US.UTF-8"},
        env_file={"HOWL_LANG": "en"},
    )
    assert lang == "pt-BR"


def test_flag_accepts_equals_form():
    assert resolve_language(argv=["howl", "--lang=pt-BR"], env={}, env_file={}) == "pt-BR"


def test_env_var_wins_over_env_file():
    lang = resolve_language(argv=["howl"], env={"HOWL_LANG": "pt-BR"}, env_file={"HOWL_LANG": "en"})
    assert lang == "pt-BR"


def test_env_file_wins_over_locale():
    lang = resolve_language(
        argv=["howl"], env={"LANG": "en_US.UTF-8"}, env_file={"HOWL_LANG": "pt-BR"}
    )
    assert lang == "pt-BR"


def test_locale_detects_brazilian_portuguese():
    assert resolve_language(argv=["howl"], env={"LANG": "pt_BR.UTF-8"}, env_file={}) == "pt-BR"


def test_locale_falls_through_for_other_languages():
    assert resolve_language(argv=["howl"], env={"LANG": "fr_FR.UTF-8"}, env_file={}) == "en"


def test_defaults_to_english():
    assert resolve_language(argv=["howl"], env={}, env_file={}) == "en"


def test_unsupported_flag_value_falls_back_to_english():
    assert resolve_language(argv=["howl", "--lang", "fr"], env={}, env_file={}) == "en"
