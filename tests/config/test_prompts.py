from unittest.mock import MagicMock, patch

import steam_hltb.config.prompts as prompts

# --- _detect_vdf_paths ---


def test_detect_vdf_paths_macos(monkeypatch, tmp_path):
    vdf = tmp_path / "Library/Application Support/Steam/userdata/123/7/remote/sharedconfig.vdf"
    vdf.parent.mkdir(parents=True)
    vdf.touch()
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setattr(prompts.Path, "home", classmethod(lambda cls: tmp_path))
    assert prompts._detect_vdf_paths() == [str(vdf)]


def test_detect_vdf_paths_linux(monkeypatch, tmp_path):
    vdf = tmp_path / ".steam/steam/userdata/123/7/remote/sharedconfig.vdf"
    vdf.parent.mkdir(parents=True)
    vdf.touch()
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr(prompts.Path, "home", classmethod(lambda cls: tmp_path))
    assert prompts._detect_vdf_paths() == [str(vdf)]


def test_detect_vdf_paths_unknown_system(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "FreeBSD")
    assert prompts._detect_vdf_paths() == []


def test_detect_vdf_paths_windows(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Windows")
    # caminho do Windows não existe no ambiente de teste → glob vazio
    assert prompts._detect_vdf_paths() == []


# --- _validate_api_key ---


def test_validate_api_key_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("requests.get", return_value=mock_resp):
        assert prompts._validate_api_key("VALIDKEY") is True


def test_validate_api_key_failure():
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    with patch("requests.get", return_value=mock_resp):
        assert prompts._validate_api_key("BADKEY") is False


def test_validate_api_key_network_error():
    with patch("requests.get", side_effect=Exception("timeout")):
        assert prompts._validate_api_key("KEY") is False


# --- _validate_username ---


def test_validate_username_found():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": {"success": 1, "steamid": "76561198012345"}}
    with patch("requests.get", return_value=mock_resp):
        result = prompts._validate_username("KEY", "gabelogannewell")
    assert result == "76561198012345"


def test_validate_username_not_found():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": {"success": 42, "message": "No match"}}
    with patch("requests.get", return_value=mock_resp):
        result = prompts._validate_username("KEY", "nonexistent")
    assert result is None


def test_validate_username_network_error():
    with patch("requests.get", side_effect=Exception("timeout")):
        assert prompts._validate_username("KEY", "user") is None


def test_validate_api_key_verbose_prints(capsys):
    resp = MagicMock()
    resp.status_code = 200
    with patch("requests.get", return_value=resp):
        assert prompts._validate_api_key("k", verbose=True) is True
    assert "debug" in capsys.readouterr().out


def test_validate_api_key_verbose_network_error(capsys):
    with patch("requests.get", side_effect=Exception("x")):
        assert prompts._validate_api_key("k", verbose=True) is False
    assert "network error" in capsys.readouterr().out


def test_validate_username_verbose_prints(capsys):
    resp = MagicMock()
    resp.json.return_value = {"response": {"success": 1, "steamid": "1"}}
    with patch("requests.get", return_value=resp):
        assert prompts._validate_username("k", "u", verbose=True) == "1"
    assert "debug" in capsys.readouterr().out


def test_validate_username_verbose_network_error(capsys):
    with patch("requests.get", side_effect=Exception("x")):
        assert prompts._validate_username("k", "u", verbose=True) is None
    assert "network error" in capsys.readouterr().out


# --- _prompt_api_key ---


def test_prompt_api_key_uses_existing_env(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "envkey")
    monkeypatch.setattr("builtins.input", lambda _: "s")  # usar a existente
    assert prompts._prompt_api_key() == "envkey"


def test_prompt_api_key_existing_rejected_then_new(monkeypatch):
    monkeypatch.setenv("STEAM_API_KEY", "old")
    monkeypatch.setattr(prompts, "_validate_api_key", lambda k, verbose=False: True)
    inputs = iter(["n", "newkey"])  # não usar existente → digita nova
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert prompts._prompt_api_key() == "newkey"


def test_prompt_api_key_retry_then_skip(monkeypatch):
    monkeypatch.delenv("STEAM_API_KEY", raising=False)
    monkeypatch.setattr(prompts, "_validate_api_key", lambda k, verbose=False: False)
    inputs = iter(["", "badkey", "n"])  # vazio→obrigatória, inválida, não tentar de novo
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert prompts._prompt_api_key() == "badkey"


def test_prompt_api_key_retries_then_succeeds(monkeypatch):
    monkeypatch.delenv("STEAM_API_KEY", raising=False)
    validations = iter([False, True])
    monkeypatch.setattr(prompts, "_validate_api_key", lambda k, verbose=False: next(validations))
    inputs = iter(["bad", "s", "good"])  # inválida, "s" tenta de novo, válida
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert prompts._prompt_api_key() == "good"


# --- _prompt_username ---


def test_prompt_username_uses_existing_env(monkeypatch):
    monkeypatch.setenv("STEAM_USERNAME", "bob")
    monkeypatch.setattr("builtins.input", lambda _: "s")
    assert prompts._prompt_username("key") == "bob"


def test_prompt_username_validates_new(monkeypatch):
    monkeypatch.delenv("STEAM_USERNAME", raising=False)
    monkeypatch.setattr(prompts, "_validate_username", lambda k, u, verbose=False: "76561")
    monkeypatch.setattr("builtins.input", lambda _: "alice")
    assert prompts._prompt_username("key") == "alice"


def test_prompt_username_retry_then_skip(monkeypatch):
    monkeypatch.delenv("STEAM_USERNAME", raising=False)
    monkeypatch.setattr(prompts, "_validate_username", lambda k, u, verbose=False: None)
    inputs = iter(["", "baduser", "n"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert prompts._prompt_username("key") == "baduser"


def test_prompt_username_existing_rejected_then_new(monkeypatch):
    monkeypatch.setenv("STEAM_USERNAME", "old")
    monkeypatch.setattr(prompts, "_validate_username", lambda k, u, verbose=False: "1")
    inputs = iter(["n", "alice"])  # não usar existente → digita novo
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert prompts._prompt_username("key") == "alice"


def test_prompt_username_retries_then_succeeds(monkeypatch):
    monkeypatch.delenv("STEAM_USERNAME", raising=False)
    validations = iter([None, "76561"])
    monkeypatch.setattr(
        prompts, "_validate_username", lambda k, u, verbose=False: next(validations)
    )
    inputs = iter(["bad", "s", "good"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert prompts._prompt_username("key") == "good"


# --- _prompt_vdf_path ---


def test_prompt_vdf_uses_existing_env(monkeypatch):
    monkeypatch.setenv("STEAM_VDF_PATH", "/x.vdf")
    monkeypatch.setattr("builtins.input", lambda _: "s")
    assert prompts._prompt_vdf_path() == "/x.vdf"


def test_prompt_vdf_existing_rejected_then_manual(monkeypatch):
    monkeypatch.setenv("STEAM_VDF_PATH", "/old.vdf")
    monkeypatch.setattr(prompts, "_detect_vdf_paths", lambda: [])
    inputs = iter(["n", "/manual.vdf"])  # rejeita existente → digita manual
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert prompts._prompt_vdf_path() == "/manual.vdf"


def test_prompt_vdf_picks_detected(monkeypatch):
    monkeypatch.delenv("STEAM_VDF_PATH", raising=False)
    monkeypatch.setattr(prompts, "_detect_vdf_paths", lambda: ["/a.vdf", "/b.vdf"])
    monkeypatch.setattr("builtins.input", lambda _: "2")
    assert prompts._prompt_vdf_path() == "/b.vdf"


def test_prompt_vdf_detected_but_skipped(monkeypatch):
    monkeypatch.delenv("STEAM_VDF_PATH", raising=False)
    monkeypatch.setattr(prompts, "_detect_vdf_paths", lambda: ["/a.vdf"])
    monkeypatch.setattr("builtins.input", lambda _: "")  # Enter pula
    assert prompts._prompt_vdf_path() is None


def test_prompt_vdf_manual_path(monkeypatch):
    monkeypatch.delenv("STEAM_VDF_PATH", raising=False)
    monkeypatch.setattr(prompts, "_detect_vdf_paths", lambda: [])
    monkeypatch.setattr("builtins.input", lambda _: "/manual.vdf")
    assert prompts._prompt_vdf_path() == "/manual.vdf"


def test_prompt_vdf_manual_empty(monkeypatch):
    monkeypatch.delenv("STEAM_VDF_PATH", raising=False)
    monkeypatch.setattr(prompts, "_detect_vdf_paths", lambda: [])
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert prompts._prompt_vdf_path() is None
