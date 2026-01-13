"""Trello REST API client for board, list, and card operations."""

from typing import Any
import requests


class TrelloAPIError(Exception):
    """Exception raised for Trello API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class TrelloClient:
    """Client for interacting with the Trello REST API."""

    BASE_URL = "https://api.trello.com/1"

    def __init__(self, api_key: str, token: str):
        """Initialize the Trello client with API credentials.

        Args:
            api_key: Trello API key
            token: Trello API token
        """
        self.api_key = api_key
        self.token = token
        self._session = requests.Session()

    def _get_auth_params(self) -> dict[str, str]:
        """Get authentication parameters for API requests."""
        return {"key": self.api_key, "token": self.token}

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated request to the Trello API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data

        Returns:
            JSON response from the API

        Raises:
            TrelloAPIError: If the API request fails
        """
        url = f"{self.BASE_URL}{endpoint}"
        request_params = self._get_auth_params()
        if params:
            request_params.update(params)

        response = None
        try:
            response = self._session.request(
                method=method,
                url=url,
                params=request_params,
                json=data,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError:
            status_code = response.status_code if response is not None else None
            error_msg = f"Trello API error: HTTP {status_code}"
            if response is not None:
                try:
                    error_detail = response.json()
                    error_msg = f"Trello API error: {error_detail}"
                except ValueError:
                    error_msg = f"Trello API error: {response.text}"
            raise TrelloAPIError(error_msg, status_code)
        except requests.exceptions.RequestException as e:
            raise TrelloAPIError(f"Request failed: {e}")

    def verify_credentials(self) -> dict[str, Any]:
        """Verify that the API credentials are valid.

        Returns:
            Member information if credentials are valid

        Raises:
            TrelloAPIError: If credentials are invalid
        """
        return self._request("GET", "/members/me")

    def create_board(
        self,
        name: str,
        description: str | None = None,
        default_lists: bool = False,
    ) -> dict[str, Any]:
        """Create a new Trello board.

        Args:
            name: Board name
            description: Board description
            default_lists: Whether to create default lists (To Do, Doing, Done)

        Returns:
            Created board data including id
        """
        params = {
            "name": name,
            "defaultLists": str(default_lists).lower(),
        }
        if description:
            params["desc"] = description
        return self._request("POST", "/boards", params=params)

    def create_list(
        self,
        board_id: str,
        name: str,
        position: str | int = "bottom",
    ) -> dict[str, Any]:
        """Create a new list on a board.

        Args:
            board_id: ID of the board to add the list to
            name: List name
            position: Position of the list (top, bottom, or numeric)

        Returns:
            Created list data including id
        """
        params = {
            "name": name,
            "idBoard": board_id,
            "pos": position,
        }
        return self._request("POST", "/lists", params=params)

    def create_card(
        self,
        list_id: str,
        name: str,
        description: str | None = None,
        position: str | int = "bottom",
        labels: list[str] | None = None,
        due_date: str | None = None,
    ) -> dict[str, Any]:
        """Create a new card in a list.

        Args:
            list_id: ID of the list to add the card to
            name: Card name
            description: Card description
            position: Position of the card (top, bottom, or numeric)
            labels: List of label IDs to attach
            due_date: Due date in ISO format

        Returns:
            Created card data including id
        """
        params: dict[str, Any] = {
            "name": name,
            "idList": list_id,
            "pos": position,
        }
        if description:
            params["desc"] = description
        if labels:
            params["idLabels"] = ",".join(labels)
        if due_date:
            params["due"] = due_date
        return self._request("POST", "/cards", params=params)

    def get_board(self, board_id: str) -> dict[str, Any]:
        """Get board details.

        Args:
            board_id: ID of the board

        Returns:
            Board data
        """
        return self._request("GET", f"/boards/{board_id}")

    def get_board_lists(self, board_id: str) -> list[dict[str, Any]]:
        """Get all lists on a board.

        Args:
            board_id: ID of the board

        Returns:
            List of list data
        """
        return self._request("GET", f"/boards/{board_id}/lists")

    def get_list_cards(self, list_id: str) -> list[dict[str, Any]]:
        """Get all cards in a list.

        Args:
            list_id: ID of the list

        Returns:
            List of card data
        """
        return self._request("GET", f"/lists/{list_id}/cards")

    def delete_board(self, board_id: str) -> None:
        """Delete a board.

        Args:
            board_id: ID of the board to delete
        """
        self._request("DELETE", f"/boards/{board_id}")

    def create_label(
        self,
        board_id: str,
        name: str,
        color: str,
    ) -> dict[str, Any]:
        """Create a label on a board.

        Args:
            board_id: ID of the board
            name: Label name
            color: Label color (yellow, purple, blue, red, green, orange, black, sky, pink, lime)

        Returns:
            Created label data including id
        """
        params = {
            "name": name,
            "color": color,
            "idBoard": board_id,
        }
        return self._request("POST", "/labels", params=params)

    def get_board_labels(self, board_id: str) -> list[dict[str, Any]]:
        """Get all labels on a board.

        Args:
            board_id: ID of the board

        Returns:
            List of label data
        """
        return self._request("GET", f"/boards/{board_id}/labels")

    def list_boards(self, filter_type: str = "open") -> list[dict[str, Any]]:
        """List all boards for the authenticated user.

        Args:
            filter_type: Filter for boards - 'all', 'open', 'closed', 'members', 'organization', 'public', 'starred'

        Returns:
            List of board data including id, name, url, and closed status
        """
        params = {"filter": filter_type}
        return self._request("GET", "/members/me/boards", params=params)

    def get_board_cards(self, board_id: str) -> list[dict[str, Any]]:
        """Get all cards on a board.

        Args:
            board_id: ID of the board

        Returns:
            List of card data including id, name, idList, and other properties
        """
        return self._request("GET", f"/boards/{board_id}/cards")

    def update_card(
        self,
        card_id: str,
        name: str | None = None,
        description: str | None = None,
        closed: bool | None = None,
        due_date: str | None = None,
        labels: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update an existing card.

        Args:
            card_id: ID of the card to update
            name: New card name
            description: New card description
            closed: Whether the card is archived
            due_date: Due date in ISO format, or empty string to remove
            labels: List of label IDs to set (replaces existing labels)

        Returns:
            Updated card data
        """
        params: dict[str, Any] = {}
        if name is not None:
            params["name"] = name
        if description is not None:
            params["desc"] = description
        if closed is not None:
            params["closed"] = str(closed).lower()
        if due_date is not None:
            params["due"] = due_date if due_date else "null"
        if labels is not None:
            params["idLabels"] = ",".join(labels) if labels else ""
        return self._request("PUT", f"/cards/{card_id}", params=params)

    def move_card(self, card_id: str, list_id: str, position: str | int = "bottom") -> dict[str, Any]:
        """Move a card to a different list.

        Args:
            card_id: ID of the card to move
            list_id: ID of the target list
            position: Position in the target list (top, bottom, or numeric)

        Returns:
            Updated card data

        Raises:
            TrelloAPIError: If the card or target list does not exist
        """
        params = {
            "idList": list_id,
            "pos": position,
        }
        return self._request("PUT", f"/cards/{card_id}", params=params)

    def delete_card(self, card_id: str) -> None:
        """Delete a card.

        Args:
            card_id: ID of the card to delete
        """
        self._request("DELETE", f"/cards/{card_id}")
