import re

import pytest

from steam_hltb.i18n import LANGUAGES, current_language, en, pt_br, set_language, t

_PLACEHOLDER = re.compile(r"{(\w+)}")


def test_catalogs_have_identical_keys():
    assert set(en.MESSAGES) == set(pt_br.MESSAGES)


def test_catalogs_have_identical_placeholders():
    for key in en.MESSAGES:
        english = set(_PLACEHOLDER.findall(en.MESSAGES[key]))
        portuguese = set(_PLACEHOLDER.findall(pt_br.MESSAGES[key]))
        assert english == portuguese, key


def test_languages_lists_both_catalogs():
    assert LANGUAGES == ("en", "pt-BR")


def test_t_returns_english_by_default():
    set_language("en")
    assert current_language() == "en"
    assert t("test.plain") == "plain english"


def test_t_interpolates_named_placeholders():
    set_language("en")
    assert t("test.interpolated", count=3) == "3 items"


def test_t_switches_catalog_with_language():
    set_language("pt-BR")
    assert t("test.plain") == "português puro"


def test_set_language_rejects_unknown_code():
    with pytest.raises(ValueError, match="unsupported language"):
        set_language("fr")
