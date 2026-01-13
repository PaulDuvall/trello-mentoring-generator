"""Tests for the Trello API client."""

import pytest
import requests
import responses
from responses import matchers

from trello_career_planner.api_client import TrelloClient, TrelloAPIError


@pytest.fixture
def client():
    """Create a test client."""
    return TrelloClient(api_key="test_api_key", token="test_token")


@pytest.fixture
def auth_params():
    """Expected auth parameters."""
    return {"key": "test_api_key", "token": "test_token"}


class TestTrelloClientInit:
    """Tests for TrelloClient initialization."""

    def test_init_stores_credentials(self):
        """Client stores API key and token."""
        client = TrelloClient(api_key="my_key", token="my_token")
        assert client.api_key == "my_key"
        assert client.token == "my_token"


class TestVerifyCredentials:
    """Tests for credential verification."""

    @responses.activate
    def test_verify_credentials_success(self, client, auth_params):
        """Returns member info on success."""
        responses.add(
            responses.GET,
            "https://api.trello.com/1/members/me",
            json={"id": "member123", "fullName": "Test User"},
            status=200,
        )

        result = client.verify_credentials()

        assert result["id"] == "member123"
        assert result["fullName"] == "Test User"

    @responses.activate
    def test_verify_credentials_invalid(self, client):
        """Raises error on invalid credentials."""
        responses.add(
            responses.GET,
            "https://api.trello.com/1/members/me",
            json={"message": "invalid token"},
            status=401,
        )

        with pytest.raises(TrelloAPIError) as exc_info:
            client.verify_credentials()

        assert exc_info.value.status_code == 401


class TestCreateBoard:
    """Tests for board creation."""

    @responses.activate
    def test_create_board_minimal(self, client):
        """Creates board with just a name."""
        responses.add(
            responses.POST,
            "https://api.trello.com/1/boards",
            json={"id": "board123", "name": "My Board", "url": "https://trello.com/b/board123"},
            status=200,
        )

        result = client.create_board(name="My Board")

        assert result["id"] == "board123"
        assert result["name"] == "My Board"

    @responses.activate
    def test_create_board_with_description(self, client):
        """Creates board with description."""
        responses.add(
            responses.POST,
            "https://api.trello.com/1/boards",
            json={"id": "board123", "name": "My Board", "desc": "A description"},
            status=200,
        )

        result = client.create_board(name="My Board", description="A description")

        assert result["id"] == "board123"

    @responses.activate
    def test_create_board_without_default_lists(self, client):
        """Creates board without default lists."""
        responses.add(
            responses.POST,
            "https://api.trello.com/1/boards",
            json={"id": "board123"},
            status=200,
        )

        client.create_board(name="My Board", default_lists=False)

        assert "defaultLists=false" in responses.calls[0].request.url


class TestCreateList:
    """Tests for list creation."""

    @responses.activate
    def test_create_list(self, client):
        """Creates a list on a board."""
        responses.add(
            responses.POST,
            "https://api.trello.com/1/lists",
            json={"id": "list123", "name": "To Do", "idBoard": "board123"},
            status=200,
        )

        result = client.create_list(board_id="board123", name="To Do")

        assert result["id"] == "list123"
        assert result["name"] == "To Do"

    @responses.activate
    def test_create_list_with_position(self, client):
        """Creates a list at specific position."""
        responses.add(
            responses.POST,
            "https://api.trello.com/1/lists",
            json={"id": "list123"},
            status=200,
        )

        client.create_list(board_id="board123", name="Middle", position="top")

        assert "pos=top" in responses.calls[0].request.url


class TestCreateCard:
    """Tests for card creation."""

    @responses.activate
    def test_create_card_minimal(self, client):
        """Creates card with just a name."""
        responses.add(
            responses.POST,
            "https://api.trello.com/1/cards",
            json={"id": "card123", "name": "My Card"},
            status=200,
        )

        result = client.create_card(list_id="list123", name="My Card")

        assert result["id"] == "card123"

    @responses.activate
    def test_create_card_with_description(self, client):
        """Creates card with description."""
        responses.add(
            responses.POST,
            "https://api.trello.com/1/cards",
            json={"id": "card123", "name": "My Card", "desc": "Details"},
            status=200,
        )

        result = client.create_card(
            list_id="list123",
            name="My Card",
            description="Details",
        )

        assert result["id"] == "card123"

    @responses.activate
    def test_create_card_with_labels(self, client):
        """Creates card with labels."""
        responses.add(
            responses.POST,
            "https://api.trello.com/1/cards",
            json={"id": "card123"},
            status=200,
        )

        client.create_card(
            list_id="list123",
            name="My Card",
            labels=["label1", "label2"],
        )

        assert "idLabels=label1%2Clabel2" in responses.calls[0].request.url


class TestCreateLabel:
    """Tests for label creation."""

    @responses.activate
    def test_create_label(self, client):
        """Creates a label on a board."""
        responses.add(
            responses.POST,
            "https://api.trello.com/1/labels",
            json={"id": "label123", "name": "Priority", "color": "red"},
            status=200,
        )

        result = client.create_label(
            board_id="board123",
            name="Priority",
            color="red",
        )

        assert result["id"] == "label123"
        assert result["name"] == "Priority"


class TestGetOperations:
    """Tests for GET operations."""

    @responses.activate
    def test_get_board(self, client):
        """Gets board details."""
        responses.add(
            responses.GET,
            "https://api.trello.com/1/boards/board123",
            json={"id": "board123", "name": "My Board"},
            status=200,
        )

        result = client.get_board("board123")

        assert result["id"] == "board123"

    @responses.activate
    def test_get_board_lists(self, client):
        """Gets lists on a board."""
        responses.add(
            responses.GET,
            "https://api.trello.com/1/boards/board123/lists",
            json=[{"id": "list1"}, {"id": "list2"}],
            status=200,
        )

        result = client.get_board_lists("board123")

        assert len(result) == 2

    @responses.activate
    def test_get_list_cards(self, client):
        """Gets cards in a list."""
        responses.add(
            responses.GET,
            "https://api.trello.com/1/lists/list123/cards",
            json=[{"id": "card1"}, {"id": "card2"}],
            status=200,
        )

        result = client.get_list_cards("list123")

        assert len(result) == 2


class TestDeleteBoard:
    """Tests for board deletion."""

    @responses.activate
    def test_delete_board(self, client):
        """Deletes a board."""
        responses.add(
            responses.DELETE,
            "https://api.trello.com/1/boards/board123",
            json={"_value": None},
            status=200,
        )

        client.delete_board("board123")

        assert len(responses.calls) == 1


class TestErrorHandling:
    """Tests for error handling."""

    @responses.activate
    def test_http_error_with_json(self, client):
        """Handles HTTP error with JSON response."""
        responses.add(
            responses.GET,
            "https://api.trello.com/1/members/me",
            json={"message": "invalid key"},
            status=401,
        )

        with pytest.raises(TrelloAPIError) as exc_info:
            client.verify_credentials()

        assert exc_info.value.status_code == 401
        assert "invalid key" in str(exc_info.value)

    @responses.activate
    def test_http_error_with_text(self, client):
        """Handles HTTP error with text response."""
        responses.add(
            responses.GET,
            "https://api.trello.com/1/members/me",
            body="Server Error",
            status=500,
        )

        with pytest.raises(TrelloAPIError) as exc_info:
            client.verify_credentials()

        assert exc_info.value.status_code == 500

    @responses.activate
    def test_connection_error(self, client):
        """Handles connection errors."""
        responses.add(
            responses.GET,
            "https://api.trello.com/1/members/me",
            body=requests.exceptions.ConnectionError("Connection refused"),
        )

        with pytest.raises(TrelloAPIError) as exc_info:
            client.verify_credentials()

        assert "Request failed" in str(exc_info.value)
