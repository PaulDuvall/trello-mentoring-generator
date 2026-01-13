"""Tests for the bulk edit module."""

import pytest
from unittest.mock import MagicMock, patch

from trello_career_planner.edit import (
    select_board,
    select_list,
    select_cards,
    add_card,
    move_cards,
    update_cards,
    delete_cards,
    show_menu,
    run_edit_session,
)
from trello_career_planner.api_client import TrelloAPIError


class TestSelectBoard:
    """Tests for the board selection function in edit mode."""

    def test_select_board_no_boards(self, capsys):
        """Returns None when no boards available."""
        mock_client = MagicMock()
        mock_client.list_boards.return_value = []

        result = select_board(mock_client)

        assert result is None
        captured = capsys.readouterr()
        assert "No open boards found" in captured.out

    def test_select_board_api_error(self, capsys):
        """Returns None on API error."""
        mock_client = MagicMock()
        mock_client.list_boards.side_effect = TrelloAPIError("API error", 500)

        result = select_board(mock_client)

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

        result = select_board(mock_client)

        assert result is None

    @patch("builtins.input", return_value="1")
    def test_select_board_valid_selection(self, mock_input, capsys):
        """Returns board dict when valid selection made."""
        mock_client = MagicMock()
        mock_client.list_boards.return_value = [
            {"id": "board1", "name": "Board 1"},
            {"id": "board2", "name": "Board 2"},
        ]

        result = select_board(mock_client)

        assert result == {"id": "board1", "name": "Board 1"}

    @patch("builtins.input", side_effect=["invalid", "1"])
    def test_select_board_invalid_then_valid(self, mock_input, capsys):
        """Handles invalid input before valid selection."""
        mock_client = MagicMock()
        mock_client.list_boards.return_value = [
            {"id": "board1", "name": "Board 1"},
        ]

        result = select_board(mock_client)

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

        result = select_board(mock_client)

        assert result is None


class TestSelectList:
    """Tests for list selection function."""

    def test_select_list_no_lists(self, capsys):
        """Returns None when no lists available."""
        result = select_list([])

        assert result is None
        captured = capsys.readouterr()
        assert "No lists available" in captured.out

    @patch("builtins.input", return_value="0")
    def test_select_list_user_cancels(self, mock_input):
        """Returns None when user cancels."""
        lists = [{"id": "list1", "name": "To Do"}]

        result = select_list(lists)

        assert result is None

    @patch("builtins.input", return_value="1")
    def test_select_list_valid_selection(self, mock_input):
        """Returns list dict when valid selection made."""
        lists = [
            {"id": "list1", "name": "To Do"},
            {"id": "list2", "name": "Done"},
        ]

        result = select_list(lists)

        assert result == {"id": "list1", "name": "To Do"}

    @patch("builtins.input", side_effect=["5", "1"])
    def test_select_list_out_of_range_then_valid(self, mock_input, capsys):
        """Handles out of range input before valid selection."""
        lists = [{"id": "list1", "name": "To Do"}]

        result = select_list(lists)

        assert result == {"id": "list1", "name": "To Do"}
        captured = capsys.readouterr()
        assert "between 0 and 1" in captured.out


class TestSelectCards:
    """Tests for card selection function."""

    def test_select_cards_no_cards(self, capsys):
        """Returns empty list when no cards available."""
        result = select_cards([])

        assert result == []
        captured = capsys.readouterr()
        assert "No cards available" in captured.out

    @patch("builtins.input", return_value="0")
    def test_select_cards_user_cancels(self, mock_input):
        """Returns empty list when user cancels immediately."""
        cards = [{"id": "card1", "name": "Task 1"}]

        result = select_cards(cards)

        assert result == []

    @patch("builtins.input", side_effect=["1", "0"])
    def test_select_cards_single_selection(self, mock_input):
        """Returns single card when one selected."""
        cards = [
            {"id": "card1", "name": "Task 1"},
            {"id": "card2", "name": "Task 2"},
        ]

        result = select_cards(cards)

        assert len(result) == 1
        assert result[0]["id"] == "card1"

    @patch("builtins.input", side_effect=["1", "2", "0"])
    def test_select_cards_multiple_selection(self, mock_input):
        """Returns multiple cards when multiple selected."""
        cards = [
            {"id": "card1", "name": "Task 1"},
            {"id": "card2", "name": "Task 2"},
        ]

        result = select_cards(cards)

        assert len(result) == 2

    @patch("builtins.input", side_effect=["1", "1", "0"])
    def test_select_cards_duplicate_selection(self, mock_input, capsys):
        """Warns when same card selected twice."""
        cards = [{"id": "card1", "name": "Task 1"}]

        result = select_cards(cards)

        assert len(result) == 1
        captured = capsys.readouterr()
        assert "already selected" in captured.out


class TestAddCard:
    """Tests for the add card handler."""

    @patch("builtins.input", return_value="0")
    def test_add_card_user_cancels_list_selection(self, mock_input):
        """Returns False when user cancels list selection."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]

        result = add_card(mock_client, "board123")

        assert result is False
        mock_client.create_card.assert_not_called()

    @patch("builtins.input", side_effect=["1", ""])
    def test_add_card_empty_name(self, mock_input, capsys):
        """Returns False when user enters empty name to exit."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]

        result = add_card(mock_client, "board123")

        assert result is False
        captured = capsys.readouterr()
        assert "Added 0 card(s)" in captured.out

    @patch("builtins.input", side_effect=["1", "New Card", "", ""])
    def test_add_card_success(self, mock_input, capsys):
        """Successfully adds a card."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]
        mock_client.create_card.return_value = {"id": "card123", "name": "New Card"}

        result = add_card(mock_client, "board123")

        assert result is True
        mock_client.create_card.assert_called_once_with(
            list_id="list1",
            name="New Card",
            description=None,
        )
        captured = capsys.readouterr()
        assert "Created:" in captured.out

    @patch("builtins.input", side_effect=["1", "New Card", "Card description", ""])
    def test_add_card_with_description(self, mock_input):
        """Adds a card with description."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]
        mock_client.create_card.return_value = {"id": "card123", "name": "New Card"}

        result = add_card(mock_client, "board123")

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

        result = add_card(mock_client, "board123")

        assert result is False
        captured = capsys.readouterr()
        assert "Failed to get lists" in captured.err

    @patch("builtins.input", side_effect=["1", "New Card", "", ""])
    def test_add_card_api_error_creating(self, mock_input, capsys):
        """Handles API error when creating card."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]
        mock_client.create_card.side_effect = TrelloAPIError("API error", 500)

        result = add_card(mock_client, "board123")

        assert result is False
        captured = capsys.readouterr()
        assert "Failed to create card" in captured.err


class TestMoveCards:
    """Tests for the move cards handler."""

    @patch("builtins.input", return_value="0")
    def test_move_cards_user_cancels_source(self, mock_input):
        """Returns False when user cancels source list selection."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]

        result = move_cards(mock_client, "board123")

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

        result = move_cards(mock_client, "board123")

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

        result = move_cards(mock_client, "board123")

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

        result = move_cards(mock_client, "board123")

        assert result is True
        mock_client.move_card.assert_called_once_with(card_id="card1", list_id="list2")
        captured = capsys.readouterr()
        assert "Moved 1 card" in captured.out


class TestUpdateCards:
    """Tests for the update cards handler."""

    @patch("builtins.input", return_value="0")
    def test_update_cards_user_cancels_list(self, mock_input):
        """Returns False when user cancels list selection."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]

        result = update_cards(mock_client, "board123")

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

        result = update_cards(mock_client, "board123")

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

        result = update_cards(mock_client, "board123")

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

        result = update_cards(mock_client, "board123")

        assert result is True
        mock_client.update_card.assert_called_once_with(
            card_id="card1", description="New description"
        )

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

        result = update_cards(mock_client, "board123")

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

        result = update_cards(mock_client, "board123")

        assert result is False
        mock_client.update_card.assert_not_called()


class TestDeleteCards:
    """Tests for the delete cards handler."""

    @patch("builtins.input", return_value="0")
    def test_delete_cards_user_cancels_list(self, mock_input):
        """Returns False when user cancels list selection."""
        mock_client = MagicMock()
        mock_client.get_board_lists.return_value = [
            {"id": "list1", "name": "To Do"},
        ]

        result = delete_cards(mock_client, "board123")

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

        result = delete_cards(mock_client, "board123")

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

        result = delete_cards(mock_client, "board123")

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

        result = delete_cards(mock_client, "board123")

        assert result is True
        assert mock_client.delete_card.call_count == 2
        captured = capsys.readouterr()
        assert "Deleted 2 card" in captured.out


class TestShowMenu:
    """Tests for the edit menu display."""

    @patch("builtins.input", return_value="1")
    def test_show_menu_returns_choice(self, mock_input, capsys):
        """Returns user's choice."""
        result = show_menu()

        assert result == "1"
        captured = capsys.readouterr()
        assert "Bulk Card Operations" in captured.out
        assert "Add cards" in captured.out
        assert "Move cards" in captured.out
        assert "Update card" in captured.out
        assert "Delete cards" in captured.out
        assert "Exit edit mode" in captured.out

    @patch("builtins.input", side_effect=KeyboardInterrupt)
    def test_show_menu_keyboard_interrupt(self, mock_input):
        """Returns '0' on keyboard interrupt."""
        result = show_menu()

        assert result == "0"


class TestRunEditSession:
    """Tests for the edit session command."""

    def test_edit_session_board_not_found(self, capsys):
        """Returns error when board not found."""
        mock_client = MagicMock()
        mock_client.get_board.side_effect = TrelloAPIError("Not found", 404)

        result = run_edit_session(mock_client, "nonexistent")

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()

    def test_edit_session_api_error(self, capsys):
        """Returns error on general API error."""
        mock_client = MagicMock()
        mock_client.get_board.side_effect = TrelloAPIError("Server error", 500)

        result = run_edit_session(mock_client, "board123")

        assert result == 1
        captured = capsys.readouterr()
        assert "Failed to get board" in captured.err

    @patch("trello_career_planner.edit.select_board")
    def test_edit_session_no_board_selected(self, mock_select, capsys):
        """Returns 0 when no board selected."""
        mock_client = MagicMock()
        mock_select.return_value = None

        result = run_edit_session(mock_client, None)

        assert result == 0
        captured = capsys.readouterr()
        assert "No board selected" in captured.out

    @patch("trello_career_planner.edit.show_menu")
    def test_edit_session_exit_immediately(self, mock_menu, capsys):
        """Returns 0 when user exits immediately."""
        mock_client = MagicMock()
        mock_client.get_board.return_value = {"id": "board123", "name": "Test Board"}
        mock_menu.return_value = "0"

        result = run_edit_session(mock_client, "board123")

        assert result == 0
        captured = capsys.readouterr()
        assert "Editing board: Test Board" in captured.out
        assert "Exiting edit mode" in captured.out

    @patch("trello_career_planner.edit.show_menu")
    @patch("trello_career_planner.edit.add_card")
    def test_edit_session_add_card_operation(self, mock_add, mock_menu):
        """Calls add card handler when option 1 selected."""
        mock_client = MagicMock()
        mock_client.get_board.return_value = {"id": "board123", "name": "Test Board"}
        mock_menu.side_effect = ["1", "0"]
        mock_add.return_value = True

        result = run_edit_session(mock_client, "board123")

        assert result == 0
        mock_add.assert_called_once_with(mock_client, "board123")

    @patch("trello_career_planner.edit.show_menu")
    @patch("trello_career_planner.edit.move_cards")
    def test_edit_session_move_cards_operation(self, mock_move, mock_menu):
        """Calls move cards handler when option 2 selected."""
        mock_client = MagicMock()
        mock_client.get_board.return_value = {"id": "board123", "name": "Test Board"}
        mock_menu.side_effect = ["2", "0"]
        mock_move.return_value = True

        result = run_edit_session(mock_client, "board123")

        assert result == 0
        mock_move.assert_called_once_with(mock_client, "board123")

    @patch("trello_career_planner.edit.show_menu")
    @patch("trello_career_planner.edit.update_cards")
    def test_edit_session_update_cards_operation(self, mock_update, mock_menu):
        """Calls update cards handler when option 3 selected."""
        mock_client = MagicMock()
        mock_client.get_board.return_value = {"id": "board123", "name": "Test Board"}
        mock_menu.side_effect = ["3", "0"]
        mock_update.return_value = True

        result = run_edit_session(mock_client, "board123")

        assert result == 0
        mock_update.assert_called_once_with(mock_client, "board123")

    @patch("trello_career_planner.edit.show_menu")
    @patch("trello_career_planner.edit.delete_cards")
    def test_edit_session_delete_cards_operation(self, mock_delete, mock_menu):
        """Calls delete cards handler when option 4 selected."""
        mock_client = MagicMock()
        mock_client.get_board.return_value = {"id": "board123", "name": "Test Board"}
        mock_menu.side_effect = ["4", "0"]
        mock_delete.return_value = True

        result = run_edit_session(mock_client, "board123")

        assert result == 0
        mock_delete.assert_called_once_with(mock_client, "board123")

    @patch("trello_career_planner.edit.show_menu")
    def test_edit_session_invalid_choice(self, mock_menu, capsys):
        """Handles invalid menu choice."""
        mock_client = MagicMock()
        mock_client.get_board.return_value = {"id": "board123", "name": "Test Board"}
        mock_menu.side_effect = ["9", "0"]

        result = run_edit_session(mock_client, "board123")

        assert result == 0
        captured = capsys.readouterr()
        assert "Invalid choice" in captured.out
