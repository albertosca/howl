from unittest.mock import MagicMock, patch

import steam_hltb.setup_prompts as prompts

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
