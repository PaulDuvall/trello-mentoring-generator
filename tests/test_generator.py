"""Tests for the board generator."""

import pytest
from unittest.mock import MagicMock, patch, call

from trello_career_planner.generator import (
    BoardGenerator,
    GeneratedBoard,
    GenerationProgress,
    create_career_board,
)
from trello_career_planner.template import (
    BoardTemplate,
    ListTemplate,
    CardTemplate,
    LabelTemplate,
)
from trello_career_planner.api_client import TrelloAPIError


@pytest.fixture
def mock_client():
    """Create a mock Trello client."""
    client = MagicMock()
    client.create_board.return_value = {
        "id": "board123",
        "url": "https://trello.com/b/board123",
    }
    client.create_label.return_value = {"id": "label123"}
    client.create_list.return_value = {"id": "list123"}
    client.create_card.return_value = {"id": "card123"}
    return client


@pytest.fixture
def simple_template():
    """Create a simple test template."""
    return BoardTemplate(
        name="Test Board",
        description="Test description",
        labels=[
            LabelTemplate(name="Priority", color="red"),
        ],
        lists=[
            ListTemplate(
                name="To Do",
                cards=[
                    CardTemplate(name="Task 1", description="Do task 1", labels=["Priority"]),
                    CardTemplate(name="Task 2", description="Do task 2"),
                ],
            ),
            ListTemplate(
                name="Done",
                cards=[
                    CardTemplate(name="Completed", description="Already done"),
                ],
            ),
        ],
    )


class TestBoardGenerator:
    """Tests for BoardGenerator class."""

    def test_init_with_client(self, mock_client):
        """Initializes with a client."""
        generator = BoardGenerator(mock_client)
        assert generator.client == mock_client

    def test_generate_creates_board(self, mock_client, simple_template):
        """Generate creates a board with correct name."""
        generator = BoardGenerator(mock_client)
        generator.generate(template=simple_template)

        mock_client.create_board.assert_called_once_with(
            name="Test Board",
            description="Test description",
            default_lists=False,
        )

    def test_generate_with_custom_name(self, mock_client, simple_template):
        """Generate uses custom board name if provided."""
        generator = BoardGenerator(mock_client)
        generator.generate(template=simple_template, board_name="Custom Name")

        mock_client.create_board.assert_called_once_with(
            name="Custom Name",
            description="Test description",
            default_lists=False,
        )

    def test_generate_creates_labels(self, mock_client, simple_template):
        """Generate creates all labels from template."""
        generator = BoardGenerator(mock_client)
        generator.generate(template=simple_template)

        mock_client.create_label.assert_called_once_with(
            board_id="board123",
            name="Priority",
            color="red",
        )

    def test_generate_creates_lists(self, mock_client, simple_template):
        """Generate creates all lists from template."""
        generator = BoardGenerator(mock_client)
        generator.generate(template=simple_template)

        assert mock_client.create_list.call_count == 2
        calls = mock_client.create_list.call_args_list
        assert calls[0] == call(board_id="board123", name="To Do")
        assert calls[1] == call(board_id="board123", name="Done")

    def test_generate_creates_cards(self, mock_client, simple_template):
        """Generate creates all cards from template."""
        generator = BoardGenerator(mock_client)
        generator.generate(template=simple_template)

        assert mock_client.create_card.call_count == 3

    def test_generate_cards_with_labels(self, mock_client, simple_template):
        """Generate attaches labels to cards."""
        generator = BoardGenerator(mock_client)
        generator.generate(template=simple_template)

        card_calls = mock_client.create_card.call_args_list
        first_card_call = card_calls[0]
        assert first_card_call == call(
            list_id="list123",
            name="Task 1",
            description="Do task 1",
            labels=["label123"],
        )

    def test_generate_returns_result(self, mock_client, simple_template):
        """Generate returns GeneratedBoard with counts."""
        generator = BoardGenerator(mock_client)
        result = generator.generate(template=simple_template)

        assert isinstance(result, GeneratedBoard)
        assert result.board_id == "board123"
        assert result.board_url == "https://trello.com/b/board123"
        assert result.board_name == "Test Board"
        assert result.lists_created == 2
        assert result.cards_created == 3
        assert result.labels_created == 1

    def test_generate_uses_default_template(self, mock_client):
        """Generate uses tech career template when none provided."""
        generator = BoardGenerator(mock_client)
        result = generator.generate()

        mock_client.create_board.assert_called_once()
        call_args = mock_client.create_board.call_args
        assert call_args[1]["name"] == "Tech Career Planning"

    def test_progress_callback_called(self, mock_client, simple_template):
        """Generate calls progress callback."""
        callback = MagicMock()
        generator = BoardGenerator(mock_client)
        generator.generate(template=simple_template, progress_callback=callback)

        assert callback.call_count > 0
        progress = callback.call_args[0][0]
        assert isinstance(progress, GenerationProgress)

    def test_handles_label_creation_error(self, mock_client, simple_template):
        """Generator continues if label creation fails."""
        mock_client.create_label.side_effect = TrelloAPIError("Label error", 400)

        generator = BoardGenerator(mock_client)
        result = generator.generate(template=simple_template)

        assert result.labels_created == 0
        assert len(generator.progress.errors) > 0

    def test_handles_list_creation_error(self, mock_client, simple_template):
        """Generator tracks errors if list creation fails."""
        mock_client.create_list.side_effect = TrelloAPIError("List error", 400)

        generator = BoardGenerator(mock_client)
        result = generator.generate(template=simple_template)

        assert result.lists_created == 0
        assert len(generator.progress.errors) > 0

    def test_handles_card_creation_error(self, mock_client, simple_template):
        """Generator continues if card creation fails."""
        mock_client.create_card.side_effect = TrelloAPIError("Card error", 400)

        generator = BoardGenerator(mock_client)
        result = generator.generate(template=simple_template)

        assert result.cards_created == 0
        assert len(generator.progress.errors) > 0


class TestCreateCareerBoard:
    """Tests for create_career_board convenience function."""

    def test_creates_board(self, mock_client):
        """Creates a tech career board."""
        result = create_career_board(mock_client)

        assert isinstance(result, GeneratedBoard)
        mock_client.create_board.assert_called_once()

    def test_accepts_custom_name(self, mock_client):
        """Accepts a custom board name."""
        create_career_board(mock_client, board_name="My Career Plan")

        call_args = mock_client.create_board.call_args
        assert call_args[1]["name"] == "My Career Plan"

    def test_verbose_mode(self, mock_client, capsys):
        """Verbose mode prints progress."""
        create_career_board(mock_client, verbose=True)

        captured = capsys.readouterr()
        assert len(captured.out) > 0


class TestGenerationProgress:
    """Tests for GenerationProgress dataclass."""

    def test_default_values(self):
        """Has sensible defaults."""
        progress = GenerationProgress()
        assert progress.total_lists == 0
        assert progress.total_cards == 0
        assert progress.lists_created == 0
        assert progress.cards_created == 0
        assert progress.current_step == ""
        assert progress.errors == []

    def test_errors_list_is_mutable(self):
        """Errors list can be appended to."""
        progress = GenerationProgress()
        progress.errors.append("Error 1")
        assert len(progress.errors) == 1


class TestGeneratedBoard:
    """Tests for GeneratedBoard dataclass."""

    def test_stores_all_values(self):
        """Stores all board generation results."""
        result = GeneratedBoard(
            board_id="id123",
            board_url="https://trello.com/b/id123",
            board_name="My Board",
            lists_created=5,
            cards_created=20,
            labels_created=4,
        )
        assert result.board_id == "id123"
        assert result.board_url == "https://trello.com/b/id123"
        assert result.board_name == "My Board"
        assert result.lists_created == 5
        assert result.cards_created == 20
        assert result.labels_created == 4
