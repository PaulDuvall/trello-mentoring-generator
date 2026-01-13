"""Tests for credential handling."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from trello_career_planner.credentials import (
    TrelloCredentials,
    CredentialError,
    load_credentials,
    validate_credentials,
    get_credentials_help,
)


class TestTrelloCredentials:
    """Tests for TrelloCredentials dataclass."""

    def test_creates_valid_credentials(self):
        """Creates credentials with valid values."""
        creds = TrelloCredentials(api_key="abc123", token="xyz789")
        assert creds.api_key == "abc123"
        assert creds.token == "xyz789"

    def test_rejects_empty_api_key(self):
        """Raises error for empty API key."""
        with pytest.raises(CredentialError, match="API key cannot be empty"):
            TrelloCredentials(api_key="", token="xyz789")

    def test_rejects_empty_token(self):
        """Raises error for empty token."""
        with pytest.raises(CredentialError, match="Token cannot be empty"):
            TrelloCredentials(api_key="abc123", token="")


class TestLoadCredentials:
    """Tests for load_credentials function."""

    def test_loads_from_explicit_args(self):
        """Loads credentials from explicit arguments."""
        creds = load_credentials(api_key="my_key", token="my_token")
        assert creds.api_key == "my_key"
        assert creds.token == "my_token"

    def test_loads_from_environment(self):
        """Loads credentials from environment variables."""
        with patch.dict(os.environ, {
            "TRELLO_API_KEY": "env_key",
            "TRELLO_TOKEN": "env_token",
        }):
            creds = load_credentials()
            assert creds.api_key == "env_key"
            assert creds.token == "env_token"

    def test_explicit_args_override_environment(self):
        """Explicit arguments take precedence over environment."""
        with patch.dict(os.environ, {
            "TRELLO_API_KEY": "env_key",
            "TRELLO_TOKEN": "env_token",
        }):
            creds = load_credentials(api_key="explicit_key", token="explicit_token")
            assert creds.api_key == "explicit_key"
            assert creds.token == "explicit_token"

    def test_partial_explicit_args(self):
        """Can mix explicit args with environment."""
        with patch.dict(os.environ, {
            "TRELLO_API_KEY": "env_key",
            "TRELLO_TOKEN": "env_token",
        }):
            creds = load_credentials(api_key="explicit_key")
            assert creds.api_key == "explicit_key"
            assert creds.token == "env_token"

    @patch("trello_career_planner.credentials.load_dotenv")
    def test_raises_when_no_api_key(self, mock_dotenv):
        """Raises error when API key not found."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(CredentialError, match="API key not found"):
                load_credentials()

    @patch("trello_career_planner.credentials.load_dotenv")
    def test_raises_when_no_token(self, mock_dotenv):
        """Raises error when token not found."""
        with patch.dict(os.environ, {"TRELLO_API_KEY": "key"}, clear=True):
            with pytest.raises(CredentialError, match="token not found"):
                load_credentials()

    def test_loads_from_env_file(self, tmp_path):
        """Loads credentials from .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("TRELLO_API_KEY=file_key\nTRELLO_TOKEN=file_token\n")

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("TRELLO_API_KEY", None)
            os.environ.pop("TRELLO_TOKEN", None)
            creds = load_credentials(env_file=str(env_file))
            assert creds.api_key == "file_key"
            assert creds.token == "file_token"

    def test_raises_for_missing_env_file(self):
        """Raises error when specified env file doesn't exist."""
        with pytest.raises(CredentialError, match="Environment file not found"):
            load_credentials(env_file="/nonexistent/.env")


class TestValidateCredentials:
    """Tests for validate_credentials function."""

    def test_validates_proper_length_credentials(self):
        """Accepts credentials with proper length."""
        creds = TrelloCredentials(
            api_key="a" * 32,
            token="b" * 64,
        )
        assert validate_credentials(creds) is True

    def test_rejects_short_api_key(self):
        """Rejects API keys that are too short."""
        creds = TrelloCredentials(api_key="short", token="b" * 64)
        with pytest.raises(CredentialError, match="API key appears too short"):
            validate_credentials(creds)

    def test_rejects_short_token(self):
        """Rejects tokens that are too short."""
        creds = TrelloCredentials(api_key="a" * 32, token="short")
        with pytest.raises(CredentialError, match="Token appears too short"):
            validate_credentials(creds)


class TestGetCredentialsHelp:
    """Tests for get_credentials_help function."""

    def test_returns_help_text(self):
        """Returns non-empty help text."""
        help_text = get_credentials_help()
        assert len(help_text) > 100

    def test_includes_api_key_instructions(self):
        """Help includes API key instructions."""
        help_text = get_credentials_help()
        assert "API Key" in help_text or "API key" in help_text
        assert "trello.com/app-key" in help_text

    def test_includes_token_instructions(self):
        """Help includes token instructions."""
        help_text = get_credentials_help()
        assert "Token" in help_text or "token" in help_text

    def test_includes_env_var_instructions(self):
        """Help includes environment variable instructions."""
        help_text = get_credentials_help()
        assert "TRELLO_API_KEY" in help_text
        assert "TRELLO_TOKEN" in help_text
