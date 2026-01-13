"""Tests for the CLI."""

import pytest
from unittest.mock import MagicMock, patch

from trello_career_planner.cli import (
    main,
    create_parser,
    select_board_for_deletion,
    confirm_deletion,
    delete_board_command,
)
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

    def test_delete_flag(self, parser):
        """Accepts -d and --delete."""
        args = parser.parse_args(["-d"])
        assert args.delete is True

        args = parser.parse_args(["--delete"])
        assert args.delete is True

    def test_board_id_flag(self, parser):
        """Accepts --board-id."""
        args = parser.parse_args(["--board-id", "abc123"])
        assert args.board_id == "abc123"

    def test_yes_flag(self, parser):
        """Accepts -y and --yes."""
        args = parser.parse_args(["-y"])
        assert args.yes is True

        args = parser.parse_args(["--yes"])
        assert args.yes is True

    def test_edit_flag(self, parser):
        """Accepts --edit flag."""
        args = parser.parse_args(["--edit"])
        assert args.edit is True

    def test_edit_flag_default_false(self, parser):
        """Edit flag defaults to False."""
        args = parser.parse_args([])
        assert args.edit is False

    def test_edit_with_board_id(self, parser):
        """Accepts --edit with --board-id."""
        args = parser.parse_args(["--edit", "--board-id", "abc123"])
        assert args.edit is True
        assert args.board_id == "abc123"


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


class TestDeleteCommand:
    """Tests for the delete board command."""

    @patch("trello_career_planner.cli.load_credentials")
    @patch("trello_career_planner.cli.validate_credentials")
    @patch("trello_career_planner.cli.TrelloClient")
    def test_delete_with_board_id_and_yes(
        self, mock_client_class, mock_validate, mock_load, capsys
    ):
        """Deletes board when --board-id and --yes provided."""
        mock_load.return_value = MagicMock(api_key="a" * 32, token="b" * 64)
        mock_validate.return_value = True
        mock_client = MagicMock()
        mock_client.get_board.return_value = {"id": "board123", "name": "Test Board"}
        mock_client_class.return_value = mock_client

        result = main(["--delete", "--board-id", "board123", "--yes"])

        assert result == 0
        mock_client.delete_board.assert_called_once_with("board123")
        captured = capsys.readouterr()
        assert "deleted successfully" in captured.out

    @patch("trello_career_planner.cli.load_credentials")
    @patch("trello_career_planner.cli.validate_credentials")
    @patch("trello_career_planner.cli.TrelloClient")
    def test_delete_board_not_found(
        self, mock_client_class, mock_validate, mock_load, capsys
    ):
        """Returns error when board not found."""
        mock_load.return_value = MagicMock(api_key="a" * 32, token="b" * 64)
        mock_validate.return_value = True
        mock_client = MagicMock()
        mock_client.get_board.side_effect = TrelloAPIError("Not found", 404)
        mock_client_class.return_value = mock_client

        result = main(["--delete", "--board-id", "nonexistent", "--yes"])

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()

    @patch("trello_career_planner.cli.load_credentials")
    @patch("trello_career_planner.cli.validate_credentials")
    @patch("trello_career_planner.cli.TrelloClient")
    @patch("trello_career_planner.cli.confirm_deletion")
    def test_delete_cancelled_by_user(
        self, mock_confirm, mock_client_class, mock_validate, mock_load, capsys
    ):
        """Returns 0 when user cancels deletion."""
        mock_load.return_value = MagicMock(api_key="a" * 32, token="b" * 64)
        mock_validate.return_value = True
        mock_client = MagicMock()
        mock_client.get_board.return_value = {"id": "board123", "name": "Test Board"}
        mock_client_class.return_value = mock_client
        mock_confirm.return_value = False

        result = main(["--delete", "--board-id", "board123"])

        assert result == 0
        mock_client.delete_board.assert_not_called()
        captured = capsys.readouterr()
        assert "cancelled" in captured.out.lower()

    @patch("trello_career_planner.cli.load_credentials")
    @patch("trello_career_planner.cli.validate_credentials")
    @patch("trello_career_planner.cli.TrelloClient")
    @patch("trello_career_planner.cli.select_board_for_deletion")
    def test_delete_interactive_no_boards(
        self, mock_select, mock_client_class, mock_validate, mock_load, capsys
    ):
        """Handles interactive mode when user cancels."""
        mock_load.return_value = MagicMock(api_key="a" * 32, token="b" * 64)
        mock_validate.return_value = True
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_select.return_value = None

        result = main(["--delete"])

        assert result == 0
        mock_client.delete_board.assert_not_called()


class TestSelectBoardForDeletion:
    """Tests for the board selection function."""

    def test_select_board_no_boards(self, capsys):
        """Returns None when no boards available."""
        mock_client = MagicMock()
        mock_client.list_boards.return_value = []

        result = select_board_for_deletion(mock_client)

        assert result is None
        captured = capsys.readouterr()
        assert "No open boards found" in captured.out

    @patch("builtins.input", return_value="0")
    def test_select_board_user_cancels(self, mock_input, capsys):
        """Returns None when user selects 0 to cancel."""
        mock_client = MagicMock()
        mock_client.list_boards.return_value = [
            {"id": "board1", "name": "Board 1"},
        ]

        result = select_board_for_deletion(mock_client)

        assert result is None

    @patch("builtins.input", return_value="1")
    def test_select_board_valid_selection(self, mock_input, capsys):
        """Returns board ID when valid selection made."""
        mock_client = MagicMock()
        mock_client.list_boards.return_value = [
            {"id": "board1", "name": "Board 1"},
            {"id": "board2", "name": "Board 2"},
        ]

        result = select_board_for_deletion(mock_client)

        assert result == "board1"


class TestConfirmDeletion:
    """Tests for the deletion confirmation function."""

    @patch("builtins.input", return_value="yes")
    def test_confirm_yes(self, mock_input):
        """Returns True for 'yes' response."""
        assert confirm_deletion("Test Board") is True

    @patch("builtins.input", return_value="y")
    def test_confirm_y(self, mock_input):
        """Returns True for 'y' response."""
        assert confirm_deletion("Test Board") is True

    @patch("builtins.input", return_value="no")
    def test_confirm_no(self, mock_input):
        """Returns False for 'no' response."""
        assert confirm_deletion("Test Board") is False

    @patch("builtins.input", return_value="")
    def test_confirm_empty(self, mock_input):
        """Returns False for empty response."""
        assert confirm_deletion("Test Board") is False

    @patch("builtins.input", side_effect=KeyboardInterrupt)
    def test_confirm_keyboard_interrupt(self, mock_input):
        """Returns False on keyboard interrupt."""
        assert confirm_deletion("Test Board") is False


class TestEditCommandIntegration:
    """Integration tests for --edit command."""

    @patch("trello_career_planner.cli.load_credentials")
    @patch("trello_career_planner.cli.validate_credentials")
    @patch("trello_career_planner.cli.TrelloClient")
    @patch("trello_career_planner.cli.edit.run_edit_session")
    def test_edit_flag_calls_edit_command(
        self, mock_edit_cmd, mock_client_class, mock_validate, mock_load
    ):
        """--edit flag invokes edit.run_edit_session."""
        mock_load.return_value = MagicMock(api_key="a" * 32, token="b" * 64)
        mock_validate.return_value = True
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_edit_cmd.return_value = 0

        result = main(["--edit"])

        assert result == 0
        mock_edit_cmd.assert_called_once_with(mock_client, None)

    @patch("trello_career_planner.cli.load_credentials")
    @patch("trello_career_planner.cli.validate_credentials")
    @patch("trello_career_planner.cli.TrelloClient")
    @patch("trello_career_planner.cli.edit.run_edit_session")
    def test_edit_with_board_id(
        self, mock_edit_cmd, mock_client_class, mock_validate, mock_load
    ):
        """--edit with --board-id passes board ID to edit command."""
        mock_load.return_value = MagicMock(api_key="a" * 32, token="b" * 64)
        mock_validate.return_value = True
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_edit_cmd.return_value = 0

        result = main(["--edit", "--board-id", "abc123"])

        assert result == 0
        mock_edit_cmd.assert_called_once_with(mock_client, "abc123")
