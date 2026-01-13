"""Tests for the CLI."""

import pytest
from unittest.mock import MagicMock, patch

from trello_career_planner.cli import main, create_parser
from trello_career_planner.generator import GeneratedBoard
from trello_career_planner.credentials import CredentialError
from trello_career_planner.api_client import TrelloAPIError


class TestArgumentParser:
    """Tests for argument parser configuration."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return create_parser()

    def test_default_values(self, parser):
        """Parser has sensible defaults."""
        args = parser.parse_args([])
        assert args.board_name is None
        assert args.api_key is None
        assert args.token is None
        assert args.verbose is False
        assert args.dry_run is False

    def test_board_name_short_flag(self, parser):
        """Accepts -n for board name."""
        args = parser.parse_args(["-n", "My Board"])
        assert args.board_name == "My Board"

    def test_board_name_long_flag(self, parser):
        """Accepts --name for board name."""
        args = parser.parse_args(["--name", "My Board"])
        assert args.board_name == "My Board"

    def test_api_key_flags(self, parser):
        """Accepts -k and --api-key."""
        args = parser.parse_args(["-k", "my_key"])
        assert args.api_key == "my_key"

        args = parser.parse_args(["--api-key", "my_key"])
        assert args.api_key == "my_key"

    def test_token_flags(self, parser):
        """Accepts -t and --token."""
        args = parser.parse_args(["-t", "my_token"])
        assert args.token == "my_token"

        args = parser.parse_args(["--token", "my_token"])
        assert args.token == "my_token"

    def test_verbose_flag(self, parser):
        """Accepts -v and --verbose."""
        args = parser.parse_args(["-v"])
        assert args.verbose is True

        args = parser.parse_args(["--verbose"])
        assert args.verbose is True

    def test_dry_run_flag(self, parser):
        """Accepts --dry-run."""
        args = parser.parse_args(["--dry-run"])
        assert args.dry_run is True

    def test_verify_only_flag(self, parser):
        """Accepts --verify-only."""
        args = parser.parse_args(["--verify-only"])
        assert args.verify_only is True

    def test_setup_help_flag(self, parser):
        """Accepts --setup-help."""
        args = parser.parse_args(["--setup-help"])
        assert args.setup_help is True

    def test_env_file_flag(self, parser):
        """Accepts -e and --env-file."""
        args = parser.parse_args(["-e", "/path/to/.env"])
        assert args.env_file == "/path/to/.env"


class TestMainFunction:
    """Tests for main CLI function."""

    def test_setup_help_returns_zero(self, capsys):
        """--setup-help returns 0 and prints help."""
        result = main(["--setup-help"])

        assert result == 0
        captured = capsys.readouterr()
        assert "API Key" in captured.out or "API key" in captured.out

    def test_dry_run_returns_zero(self, capsys):
        """--dry-run returns 0 and prints template info."""
        result = main(["--dry-run"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Tech Career Planning" in captured.out
        assert "lists" in captured.out.lower()

    @patch("trello_career_planner.cli.load_credentials")
    def test_credential_error_returns_one(self, mock_load, capsys):
        """Returns 1 when credentials are missing."""
        mock_load.side_effect = CredentialError("No API key")

        result = main([])

        assert result == 1
        captured = capsys.readouterr()
        assert "No API key" in captured.err

    @patch("trello_career_planner.cli.load_credentials")
    @patch("trello_career_planner.cli.validate_credentials")
    def test_invalid_credentials_returns_one(self, mock_validate, mock_load, capsys):
        """Returns 1 when credentials are invalid format."""
        mock_load.return_value = MagicMock(api_key="short", token="short")
        mock_validate.side_effect = CredentialError("Too short")

        result = main([])

        assert result == 1
        captured = capsys.readouterr()
        assert "Too short" in captured.err

    @patch("trello_career_planner.cli.load_credentials")
    @patch("trello_career_planner.cli.validate_credentials")
    @patch("trello_career_planner.cli.TrelloClient")
    def test_verify_only_success(self, mock_client_class, mock_validate, mock_load, capsys):
        """--verify-only returns 0 on success."""
        mock_load.return_value = MagicMock(api_key="a" * 32, token="b" * 64)
        mock_validate.return_value = True
        mock_client = MagicMock()
        mock_client.verify_credentials.return_value = {"fullName": "Test User"}
        mock_client_class.return_value = mock_client

        result = main(["--verify-only"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Test User" in captured.out

    @patch("trello_career_planner.cli.load_credentials")
    @patch("trello_career_planner.cli.validate_credentials")
    @patch("trello_career_planner.cli.TrelloClient")
    def test_verify_only_failure(self, mock_client_class, mock_validate, mock_load, capsys):
        """--verify-only returns 1 on API error."""
        mock_load.return_value = MagicMock(api_key="a" * 32, token="b" * 64)
        mock_validate.return_value = True
        mock_client = MagicMock()
        mock_client.verify_credentials.side_effect = TrelloAPIError("Invalid", 401)
        mock_client_class.return_value = mock_client

        result = main(["--verify-only"])

        assert result == 1

    @patch("trello_career_planner.cli.load_credentials")
    @patch("trello_career_planner.cli.validate_credentials")
    @patch("trello_career_planner.cli.TrelloClient")
    @patch("trello_career_planner.cli.create_career_board")
    def test_successful_board_creation(
        self, mock_create, mock_client_class, mock_validate, mock_load, capsys
    ):
        """Returns 0 on successful board creation."""
        mock_load.return_value = MagicMock(api_key="a" * 32, token="b" * 64)
        mock_validate.return_value = True
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_create.return_value = GeneratedBoard(
            board_id="board123",
            board_url="https://trello.com/b/board123",
            board_name="Tech Career Planning",
            lists_created=7,
            cards_created=30,
            labels_created=6,
        )

        result = main([])

        assert result == 0
        captured = capsys.readouterr()
        assert "Board created successfully" in captured.out
        assert "Tech Career Planning" in captured.out
        assert "https://trello.com/b/board123" in captured.out

    @patch("trello_career_planner.cli.load_credentials")
    @patch("trello_career_planner.cli.validate_credentials")
    @patch("trello_career_planner.cli.TrelloClient")
    @patch("trello_career_planner.cli.create_career_board")
    def test_custom_board_name(
        self, mock_create, mock_client_class, mock_validate, mock_load
    ):
        """Passes custom board name to generator."""
        mock_load.return_value = MagicMock(api_key="a" * 32, token="b" * 64)
        mock_validate.return_value = True
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_create.return_value = GeneratedBoard(
            board_id="b", board_url="u", board_name="Custom",
            lists_created=1, cards_created=1, labels_created=1,
        )

        main(["--name", "Custom Board Name"])

        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["board_name"] == "Custom Board Name"

    @patch("trello_career_planner.cli.load_credentials")
    @patch("trello_career_planner.cli.validate_credentials")
    @patch("trello_career_planner.cli.TrelloClient")
    @patch("trello_career_planner.cli.create_career_board")
    def test_api_error_returns_one(
        self, mock_create, mock_client_class, mock_validate, mock_load, capsys
    ):
        """Returns 1 on Trello API error."""
        mock_load.return_value = MagicMock(api_key="a" * 32, token="b" * 64)
        mock_validate.return_value = True
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_create.side_effect = TrelloAPIError("Board limit reached", 400)

        result = main([])

        assert result == 1
        captured = capsys.readouterr()
        assert "Trello API error" in captured.err

    @patch("trello_career_planner.cli.load_credentials")
    @patch("trello_career_planner.cli.validate_credentials")
    @patch("trello_career_planner.cli.TrelloClient")
    @patch("trello_career_planner.cli.create_career_board")
    def test_verbose_mode(
        self, mock_create, mock_client_class, mock_validate, mock_load, capsys
    ):
        """Verbose mode prints additional output."""
        mock_load.return_value = MagicMock(api_key="a" * 32, token="b" * 64)
        mock_validate.return_value = True
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_create.return_value = GeneratedBoard(
            board_id="b", board_url="u", board_name="Board",
            lists_created=1, cards_created=1, labels_created=1,
        )

        main(["--verbose"])

        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["verbose"] is True
