"""Tests for the CLI."""

import pytest
from unittest.mock import MagicMock, patch

from trello_career_planner.cli import (
    main,
    create_parser,
    select_board_for_deletion,
    confirm_deletion,
    delete_board_command,
    select_board_for_editing,
    select_list_from_board,
    select_cards_from_list,
    handle_add_card,
    handle_move_cards,
    handle_update_cards,
    handle_delete_cards,
    show_edit_menu,
    edit_board_command,
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


class TestEditArgumentParser:
    """Tests for --edit argument parser configuration."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return create_parser()

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


class TestSelectBoardForEditing:
    """Tests for the board selection function in edit mode."""

    def test_select_board_no_boards(self, capsys):
        """Returns None when no boards available."""
        mock_client = MagicMock()
        mock_client.list_boards.return_value = []

        result = select_board_for_editing(mock_client)

        assert result is None
        captured = capsys.readouterr()
        assert "No open boards found" in captured.out

    def test_select_board_api_error(self, capsys):
        """Returns None on API error."""
        mock_client = MagicMock()
        mock_client.list_boards.side_effect = TrelloAPIError("API error", 500)

        result = select_board_for_editing(mock_client)

        assert result is None
        captured = capsys.readouterr()
        assert "Failed to list boards" in captured.err

    @patch("builtins.input", return_value="0")
    def test_select_board_user_cancels(self, mock_input, capsys):
        """Returns None when user selects 0 to cancel."""
        mock_client = MagicMock()
        mock_client.list_boards.return_value = [
            {"id": "board1", "name": "Board 1"},
        ]

        result = select_board_for_editing(mock_client)

        assert result is None

    @patch("builtins.input", return_value="1")
    def test_select_board_valid_selection(self, mock_input, capsys):
        """Returns board dict when valid selection made."""
        mock_client = MagicMock()
        mock_client.list_boards.return_value = [
            {"id": "board1", "name": "Board 1"},
            {"id": "board2", "name": "Board 2"},
        ]

        result = select_board_for_editing(mock_client)

        assert result == {"id": "board1", "name": "Board 1"}

    @patch("builtins.input", side_effect=["invalid", "1"])
    def test_select_board_invalid_then_valid(self, mock_input, capsys):
        """Handles invalid input before valid selection."""
        mock_client = MagicMock()
        mock_client.list_boards.return_value = [
            {"id": "board1", "name": "Board 1"},
        ]

        result = select_board_for_editing(mock_client)

        assert result == {"id": "board1", "name": "Board 1"}
        captured = capsys.readouterr()
        assert "valid number" in captured.out

    @patch("builtins.input", side_effect=KeyboardInterrupt)
    def test_select_board_keyboard_interrupt(self, mock_input):
        """Returns None on keyboard interrupt."""
        mock_client = MagicMock()
        mock_client.list_boards.return_value = [
            {"id": "board1", "name": "Board 1"},
        ]

        result = select_board_for_editing(mock_client)

        assert result is None


class TestSelectListFromBoard:
    """Tests for list selection function."""

    def test_select_list_no_lists(self, capsys):
        """Returns None when no lists available."""
        result = select_list_from_board([])

        assert result is None
        captured = capsys.readouterr()
        assert "No lists available" in captured.out

    @patch("builtins.input", return_value="0")
    def test_select_list_user_cancels(self, mock_input):
        """Returns None when user cancels."""
        lists = [{"id": "list1", "name": "To Do"}]

        result = select_list_from_board(lists)

        assert result is None

    @patch("builtins.input", return_value="1")
    def test_select_list_valid_selection(self, mock_input):
        """Returns list dict when valid selection made."""
        lists = [
            {"id": "list1", "name": "To Do"},
            {"id": "list2", "name": "Done"},
        ]

        result = select_list_from_board(lists)

        assert result == {"id": "list1", "name": "To Do"}

    @patch("builtins.input", side_effect=["5", "1"])
    def test_select_list_out_of_range_then_valid(self, mock_input, capsys):
        """Handles out of range input before valid selection."""
        lists = [{"id": "list1", "name": "To Do"}]

        result = select_list_from_board(lists)

        assert result == {"id": "list1", "name": "To Do"}
        captured = capsys.readouterr()
        assert "between 0 and 1" in captured.out


class TestSelectCardsFromList:
    """Tests for card selection function."""

    def test_select_cards_no_cards(self, capsys):
        """Returns empty list when no cards available."""
        result = select_cards_from_list([])

        assert result == []
        captured = capsys.readouterr()
        assert "No cards available" in captured.out

    @patch("builtins.input", return_value="0")
    def test_select_cards_user_cancels(self, mock_input):
        """Returns empty list when user cancels immediately."""
        cards = [{"id": "card1", "name": "Task 1"}]

        result = select_cards_from_list(cards)

        assert result == []

    @patch("builtins.input", side_effect=["1", "0"])
    def test_select_cards_single_selection(self, mock_input):
        """Returns single card when one selected."""
        cards = [
            {"id": "card1", "name": "Task 1"},
            {"id": "card2", "name": "Task 2"},
        ]

        result = select_cards_from_list(cards)

        assert len(result) == 1
        assert result[0]["id"] == "card1"

    @patch("builtins.input", side_effect=["1", "2", "0"])
    def test_select_cards_multiple_selection(self, mock_input):
        """Returns multiple cards when multiple selected."""
        cards = [
            {"id": "card1", "name": "Task 1"},
            {"id": "card2", "name": "Task 2"},
        ]

        result = select_cards_from_list(cards)

        assert len(result) == 2

    @patch("builtins.input", side_effect=["1", "1", "0"])
    def test_select_cards_duplicate_selection(self, mock_input, capsys):
        """Warns when same card selected twice."""
        cards = [{"id": "card1", "name": "Task 1"}]

        result = select_cards_from_list(cards)

        assert len(result) == 1
        captured = capsys.readouterr()
        assert "already selected" in captured.out


class TestHandleAddCard:
    """Tests for the add card handler."""

    @patch("builtins.input", return_value="0")
    def test_add_card_user_cancels_list_selection(self, mock_input):
        """Returns False when user cancels list selection."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]

        result = handle_add_card(mock_client, "board123")

        assert result is False
        mock_client.create_card.assert_not_called()

    @patch("builtins.input", side_effect=["1", "", ""])
    def test_add_card_empty_name(self, mock_input, capsys):
        """Returns False when card name is empty."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]

        result = handle_add_card(mock_client, "board123")

        assert result is False
        captured = capsys.readouterr()
        assert "cannot be empty" in captured.out

    @patch("builtins.input", side_effect=["1", "New Card", ""])
    def test_add_card_success(self, mock_input, capsys):
        """Successfully adds a card."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]
        mock_client.create_card.return_value = {"id": "card123", "name": "New Card"}

        result = handle_add_card(mock_client, "board123")

        assert result is True
        mock_client.create_card.assert_called_once_with(
            list_id="list1",
            name="New Card",
            description=None,
        )
        captured = capsys.readouterr()
        assert "created successfully" in captured.out

    @patch("builtins.input", side_effect=["1", "New Card", "Card description"])
    def test_add_card_with_description(self, mock_input):
        """Adds a card with description."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]
        mock_client.create_card.return_value = {"id": "card123", "name": "New Card"}

        result = handle_add_card(mock_client, "board123")

        assert result is True
        mock_client.create_card.assert_called_once_with(
            list_id="list1",
            name="New Card",
            description="Card description",
        )

    def test_add_card_api_error_getting_lists(self, capsys):
        """Handles API error when getting lists."""
        mock_client = MagicMock()
        mock_client.get_board_lists.side_effect = TrelloAPIError("API error", 500)

        result = handle_add_card(mock_client, "board123")

        assert result is False
        captured = capsys.readouterr()
        assert "Failed to get lists" in captured.err

    @patch("builtins.input", side_effect=["1", "New Card", ""])
    def test_add_card_api_error_creating(self, mock_input, capsys):
        """Handles API error when creating card."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]
        mock_client.create_card.side_effect = TrelloAPIError("API error", 500)

        result = handle_add_card(mock_client, "board123")

        assert result is False
        captured = capsys.readouterr()
        assert "Failed to create card" in captured.err


class TestHandleMoveCards:
    """Tests for the move cards handler."""

    @patch("builtins.input", return_value="0")
    def test_move_cards_user_cancels_source(self, mock_input):
        """Returns False when user cancels source list selection."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]

        result = handle_move_cards(mock_client, "board123")

        assert result is False

    @patch("builtins.input", side_effect=["1", "0"])
    def test_move_cards_no_cards_selected(self, mock_input, capsys):
        """Returns False when no cards selected."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]
        mock_client.get_list_cards.return_value = [
            {"id": "card1", "name": "Task 1"},
        ]

        result = handle_move_cards(mock_client, "board123")

        assert result is False
        captured = capsys.readouterr()
        assert "No cards selected" in captured.out

    @patch("builtins.input", side_effect=["1", "1", "0", "1"])
    def test_move_cards_same_list(self, mock_input, capsys):
        """Returns False when source and target are same."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]
        mock_client.get_list_cards.return_value = [
            {"id": "card1", "name": "Task 1"},
        ]

        result = handle_move_cards(mock_client, "board123")

        assert result is False
        captured = capsys.readouterr()
        assert "same" in captured.out.lower()

    @patch("builtins.input", side_effect=["1", "1", "0", "2"])
    def test_move_cards_success(self, mock_input, capsys):
        """Successfully moves cards."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
            {"id": "list2", "name": "Done"},
        ]
        mock_client.get_list_cards.return_value = [
            {"id": "card1", "name": "Task 1"},
        ]

        result = handle_move_cards(mock_client, "board123")

        assert result is True
        mock_client.move_card.assert_called_once_with(card_id="card1", list_id="list2")
        captured = capsys.readouterr()
        assert "Moved 1 card" in captured.out


class TestHandleUpdateCards:
    """Tests for the update cards handler."""

    @patch("builtins.input", return_value="0")
    def test_update_cards_user_cancels_list(self, mock_input):
        """Returns False when user cancels list selection."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]

        result = handle_update_cards(mock_client, "board123")

        assert result is False

    @patch("builtins.input", side_effect=["1", "1", "0", "0"])
    def test_update_cards_user_cancels_operation(self, mock_input):
        """Returns False when user cancels operation selection."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]
        mock_client.get_list_cards.return_value = [
            {"id": "card1", "name": "Task 1"},
        ]

        result = handle_update_cards(mock_client, "board123")

        assert result is False
        mock_client.update_card.assert_not_called()

    @patch("builtins.input", side_effect=["1", "1", "0", "1", "New Name"])
    def test_update_cards_rename(self, mock_input, capsys):
        """Successfully renames cards."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]
        mock_client.get_list_cards.return_value = [
            {"id": "card1", "name": "Task 1"},
        ]

        result = handle_update_cards(mock_client, "board123")

        assert result is True
        mock_client.update_card.assert_called_once_with(card_id="card1", name="New Name")
        captured = capsys.readouterr()
        assert "Updated 1 card" in captured.out

    @patch("builtins.input", side_effect=["1", "1", "0", "2", "New description"])
    def test_update_cards_description(self, mock_input, capsys):
        """Successfully updates card descriptions."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]
        mock_client.get_list_cards.return_value = [
            {"id": "card1", "name": "Task 1"},
        ]

        result = handle_update_cards(mock_client, "board123")

        assert result is True
        mock_client.update_card.assert_called_once_with(card_id="card1", description="New description")

    @patch("builtins.input", side_effect=["1", "1", "0", "3", "yes"])
    def test_update_cards_archive(self, mock_input, capsys):
        """Successfully archives cards."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]
        mock_client.get_list_cards.return_value = [
            {"id": "card1", "name": "Task 1"},
        ]

        result = handle_update_cards(mock_client, "board123")

        assert result is True
        mock_client.update_card.assert_called_once_with(card_id="card1", closed=True)

    @patch("builtins.input", side_effect=["1", "1", "0", "3", "no"])
    def test_update_cards_archive_cancelled(self, mock_input, capsys):
        """Does not archive when user says no."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]
        mock_client.get_list_cards.return_value = [
            {"id": "card1", "name": "Task 1"},
        ]

        result = handle_update_cards(mock_client, "board123")

        assert result is False
        mock_client.update_card.assert_not_called()


class TestHandleDeleteCards:
    """Tests for the delete cards handler."""

    @patch("builtins.input", return_value="0")
    def test_delete_cards_user_cancels_list(self, mock_input):
        """Returns False when user cancels list selection."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]

        result = handle_delete_cards(mock_client, "board123")

        assert result is False

    @patch("builtins.input", side_effect=["1", "1", "0", "no"])
    def test_delete_cards_user_declines_confirm(self, mock_input, capsys):
        """Returns False when user declines confirmation."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]
        mock_client.get_list_cards.return_value = [
            {"id": "card1", "name": "Task 1"},
        ]

        result = handle_delete_cards(mock_client, "board123")

        assert result is False
        mock_client.delete_card.assert_not_called()
        captured = capsys.readouterr()
        assert "cancelled" in captured.out.lower()

    @patch("builtins.input", side_effect=["1", "1", "0", "yes"])
    def test_delete_cards_success(self, mock_input, capsys):
        """Successfully deletes cards."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]
        mock_client.get_list_cards.return_value = [
            {"id": "card1", "name": "Task 1"},
        ]

        result = handle_delete_cards(mock_client, "board123")

        assert result is True
        mock_client.delete_card.assert_called_once_with("card1")
        captured = capsys.readouterr()
        assert "Deleted 1 card" in captured.out

    @patch("builtins.input", side_effect=["1", "1", "2", "0", "yes"])
    def test_delete_multiple_cards(self, mock_input, capsys):
        """Successfully deletes multiple cards."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]
        mock_client.get_list_cards.return_value = [
            {"id": "card1", "name": "Task 1"},
            {"id": "card2", "name": "Task 2"},
        ]

        result = handle_delete_cards(mock_client, "board123")

        assert result is True
        assert mock_client.delete_card.call_count == 2
        captured = capsys.readouterr()
        assert "Deleted 2 card" in captured.out


class TestShowEditMenu:
    """Tests for the edit menu display."""

    @patch("builtins.input", return_value="1")
    def test_show_edit_menu_returns_choice(self, mock_input, capsys):
        """Returns user's choice."""
        result = show_edit_menu()

        assert result == "1"
        captured = capsys.readouterr()
        assert "Bulk Card Operations" in captured.out
        assert "Add a new card" in captured.out
        assert "Move cards" in captured.out
        assert "Update card" in captured.out
        assert "Delete cards" in captured.out
        assert "Exit edit mode" in captured.out

    @patch("builtins.input", side_effect=KeyboardInterrupt)
    def test_show_edit_menu_keyboard_interrupt(self, mock_input):
        """Returns '0' on keyboard interrupt."""
        result = show_edit_menu()

        assert result == "0"


class TestEditBoardCommand:
    """Tests for the edit board command."""

    def test_edit_board_not_found(self, capsys):
        """Returns error when board not found."""
        mock_client = MagicMock()
        mock_client.get_board.side_effect = TrelloAPIError("Not found", 404)

        result = edit_board_command(mock_client, "nonexistent")

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()

    def test_edit_board_api_error(self, capsys):
        """Returns error on general API error."""
        mock_client = MagicMock()
        mock_client.get_board.side_effect = TrelloAPIError("Server error", 500)

        result = edit_board_command(mock_client, "board123")

        assert result == 1
        captured = capsys.readouterr()
        assert "Failed to get board" in captured.err

    @patch("trello_career_planner.cli.select_board_for_editing")
    def test_edit_board_no_board_selected(self, mock_select, capsys):
        """Returns 0 when no board selected."""
        mock_client = MagicMock()
        mock_select.return_value = None

        result = edit_board_command(mock_client, None)

        assert result == 0
        captured = capsys.readouterr()
        assert "No board selected" in captured.out

    @patch("trello_career_planner.cli.show_edit_menu")
    def test_edit_board_exit_immediately(self, mock_menu, capsys):
        """Returns 0 when user exits immediately."""
        mock_client = MagicMock()
        mock_client.get_board.return_value = {"id": "board123", "name": "Test Board"}
        mock_menu.return_value = "0"

        result = edit_board_command(mock_client, "board123")

        assert result == 0
        captured = capsys.readouterr()
        assert "Editing board: Test Board" in captured.out
        assert "Exiting edit mode" in captured.out

    @patch("trello_career_planner.cli.show_edit_menu")
    @patch("trello_career_planner.cli.handle_add_card")
    def test_edit_board_add_card_operation(self, mock_add, mock_menu):
        """Calls add card handler when option 1 selected."""
        mock_client = MagicMock()
        mock_client.get_board.return_value = {"id": "board123", "name": "Test Board"}
        mock_menu.side_effect = ["1", "0"]
        mock_add.return_value = True

        result = edit_board_command(mock_client, "board123")

        assert result == 0
        mock_add.assert_called_once_with(mock_client, "board123")

    @patch("trello_career_planner.cli.show_edit_menu")
    @patch("trello_career_planner.cli.handle_move_cards")
    def test_edit_board_move_cards_operation(self, mock_move, mock_menu):
        """Calls move cards handler when option 2 selected."""
        mock_client = MagicMock()
        mock_client.get_board.return_value = {"id": "board123", "name": "Test Board"}
        mock_menu.side_effect = ["2", "0"]
        mock_move.return_value = True

        result = edit_board_command(mock_client, "board123")

        assert result == 0
        mock_move.assert_called_once_with(mock_client, "board123")

    @patch("trello_career_planner.cli.show_edit_menu")
    @patch("trello_career_planner.cli.handle_update_cards")
    def test_edit_board_update_cards_operation(self, mock_update, mock_menu):
        """Calls update cards handler when option 3 selected."""
        mock_client = MagicMock()
        mock_client.get_board.return_value = {"id": "board123", "name": "Test Board"}
        mock_menu.side_effect = ["3", "0"]
        mock_update.return_value = True

        result = edit_board_command(mock_client, "board123")

        assert result == 0
        mock_update.assert_called_once_with(mock_client, "board123")

    @patch("trello_career_planner.cli.show_edit_menu")
    @patch("trello_career_planner.cli.handle_delete_cards")
    def test_edit_board_delete_cards_operation(self, mock_delete, mock_menu):
        """Calls delete cards handler when option 4 selected."""
        mock_client = MagicMock()
        mock_client.get_board.return_value = {"id": "board123", "name": "Test Board"}
        mock_menu.side_effect = ["4", "0"]
        mock_delete.return_value = True

        result = edit_board_command(mock_client, "board123")

        assert result == 0
        mock_delete.assert_called_once_with(mock_client, "board123")

    @patch("trello_career_planner.cli.show_edit_menu")
    def test_edit_board_invalid_choice(self, mock_menu, capsys):
        """Handles invalid menu choice."""
        mock_client = MagicMock()
        mock_client.get_board.return_value = {"id": "board123", "name": "Test Board"}
        mock_menu.side_effect = ["9", "0"]

        result = edit_board_command(mock_client, "board123")

        assert result == 0
        captured = capsys.readouterr()
        assert "Invalid choice" in captured.out


class TestEditCommandIntegration:
    """Integration tests for --edit command."""

    @patch("trello_career_planner.cli.load_credentials")
    @patch("trello_career_planner.cli.validate_credentials")
    @patch("trello_career_planner.cli.TrelloClient")
    @patch("trello_career_planner.cli.edit_board_command")
    def test_edit_flag_calls_edit_command(
        self, mock_edit_cmd, mock_client_class, mock_validate, mock_load
    ):
        """--edit flag invokes edit_board_command."""
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
    @patch("trello_career_planner.cli.edit_board_command")
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
