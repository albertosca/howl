import glob
import os
import pytest
from unittest.mock import patch, MagicMock

import steam_hltb.setup as setup


# --- _detect_vdf_paths ---

def test_detect_vdf_paths_macos(monkeypatch, tmp_path):
    vdf = tmp_path / "sharedconfig.vdf"
    vdf.touch()
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    with patch("glob.glob", return_value=[str(vdf)]) as mock_glob:
        result = setup._detect_vdf_paths()
    assert result == [str(vdf)]
    called_pattern = mock_glob.call_args[0][0]
    assert "Library/Application Support/Steam" in called_pattern


def test_detect_vdf_paths_linux(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Linux")
    with patch("glob.glob", return_value=[]) as mock_glob:
        setup._detect_vdf_paths()
    called_pattern = mock_glob.call_args[0][0]
    assert ".steam/steam" in called_pattern


def test_detect_vdf_paths_unknown_system(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "FreeBSD")
    result = setup._detect_vdf_paths()
    assert result == []


# --- _validate_api_key ---

def test_validate_api_key_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("requests.get", return_value=mock_resp):
        assert setup._validate_api_key("VALIDKEY") is True


def test_validate_api_key_failure():
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    with patch("requests.get", return_value=mock_resp):
        assert setup._validate_api_key("BADKEY") is False


def test_validate_api_key_network_error():
    with patch("requests.get", side_effect=Exception("timeout")):
        assert setup._validate_api_key("KEY") is False


# --- _validate_username ---

def test_validate_username_found():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": {"success": 1, "steamid": "76561198012345"}}
    with patch("requests.get", return_value=mock_resp):
        result = setup._validate_username("KEY", "heenett")
    assert result == "76561198012345"


def test_validate_username_not_found():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": {"success": 42, "message": "No match"}}
    with patch("requests.get", return_value=mock_resp):
        result = setup._validate_username("KEY", "nonexistent")
    assert result is None


def test_validate_username_network_error():
    with patch("requests.get", side_effect=Exception("timeout")):
        assert setup._validate_username("KEY", "user") is None


# --- _write_env ---

def test_write_env_creates_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = setup._write_env({"STEAM_API_KEY": "ABC123", "STEAM_USERNAME": "heenett"})
    content = open(path).read()
    assert "STEAM_API_KEY=ABC123" in content
    assert "STEAM_USERNAME=heenett" in content


def test_write_env_merges_with_existing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("EXISTING_VAR=old\nSTEAM_API_KEY=old_key\n")
    setup._write_env({"STEAM_API_KEY": "new_key"})
    content = open(tmp_path / ".env").read()
    assert "EXISTING_VAR=old" in content
    assert "STEAM_API_KEY=new_key" in content
    assert "old_key" not in content
