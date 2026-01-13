"""Interactive bulk editing functionality for Trello boards."""

import sys

from .api_client import TrelloClient, TrelloAPIError


def select_board(client: TrelloClient) -> dict | None:
    """Display boards and let user select one for editing.

    Args:
        client: TrelloClient instance

    Returns:
        Board data dict if selected, None if cancelled
    """
    try:
        boards = client.list_boards(filter_type="open")
    except TrelloAPIError as e:
        print(f"Failed to list boards: {e}", file=sys.stderr)
        return None

    if not boards:
        print("No open boards found.")
        return None

    return _prompt_selection(boards, "edit")


def _prompt_selection(boards: list[dict], action: str) -> dict | None:
    """Prompt user to select a board from list.

    Args:
        boards: List of board dicts
        action: Action description for prompt

    Returns:
        Selected board dict or None if cancelled
    """
    print("\nYour Trello boards:")
    for i, board in enumerate(boards, 1):
        print(f"  {i}. {board['name']}")
    print("  0. Cancel")

    while True:
        try:
            choice = input(f"\nSelect a board number to {action}: ").strip()
            if choice == "0":
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(boards):
                return boards[idx]
            print(f"Please enter a number between 0 and {len(boards)}")
        except ValueError:
            print("Please enter a valid number")
        except (EOFError, KeyboardInterrupt):
            return None


def select_list(lists: list[dict], prompt: str = "Select a list") -> dict | None:
    """Display lists and let user select one.

    Args:
        lists: List of list data dicts
        prompt: Prompt message to display

    Returns:
        List data dict if selected, None if cancelled
    """
    if not lists:
        print("No lists available.")
        return None

    print(f"\n{prompt}:")
    for i, lst in enumerate(lists, 1):
        print(f"  {i}. {lst['name']}")
    print("  0. Cancel")

    return _get_numeric_choice(lists)


def _get_numeric_choice(items: list[dict]) -> dict | None:
    """Get numeric choice from user for a list of items.

    Args:
        items: List of item dicts

    Returns:
        Selected item dict or None if cancelled
    """
    while True:
        try:
            choice = input("\nEnter list number: ").strip()
            if choice == "0":
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                return items[idx]
            print(f"Please enter a number between 0 and {len(items)}")
        except ValueError:
            print("Please enter a valid number")
        except (EOFError, KeyboardInterrupt):
            return None


def select_cards(cards: list[dict], prompt: str = "Select cards") -> list[dict]:
    """Display cards and let user select multiple.

    Args:
        cards: List of card data dicts
        prompt: Prompt message to display

    Returns:
        List of selected card dicts (may be empty)
    """
    if not cards:
        print("No cards available.")
        return []

    _display_cards(cards, prompt)
    return _collect_card_selections(cards)


def _display_cards(cards: list[dict], prompt: str) -> None:
    """Display cards with numbered list."""
    print(f"\n{prompt}:")
    for i, card in enumerate(cards, 1):
        print(f"  {i}. {card['name']}")
    print("  0. Cancel / Done selecting")


def _collect_card_selections(cards: list[dict]) -> list[dict]:
    """Collect card selections from user input."""
    selected = []
    selected_indices = set()

    while True:
        try:
            choice = input("\nEnter card number (0 when done): ").strip()
            if choice == "0":
                break
            idx = int(choice) - 1
            if 0 <= idx < len(cards):
                if idx in selected_indices:
                    print(f"Card '{cards[idx]['name']}' already selected")
                else:
                    selected_indices.add(idx)
                    selected.append(cards[idx])
                    print(f"Selected: {cards[idx]['name']} ({len(selected)} total)")
            else:
                print(f"Please enter a number between 0 and {len(cards)}")
        except ValueError:
            print("Please enter a valid number")
        except (EOFError, KeyboardInterrupt):
            break

    return selected


def add_card(client: TrelloClient, board_id: str) -> bool:
    """Handle adding a new card to a list.

    Args:
        client: TrelloClient instance
        board_id: ID of the board

    Returns:
        True if card was added, False otherwise
    """
    lists = _get_board_lists(client, board_id)
    if lists is None:
        return False

    selected_list = select_list(lists, "Select a list to add card to")
    if not selected_list:
        return False

    return _create_card_interactive(client, selected_list["id"])


def _get_board_lists(client: TrelloClient, board_id: str) -> list[dict] | None:
    """Get board lists with error handling."""
    try:
        return client.get_board_lists(board_id)
    except TrelloAPIError as e:
        print(f"Failed to get lists: {e}", file=sys.stderr)
        return None


def _create_card_interactive(client: TrelloClient, list_id: str) -> bool:
    """Create card with interactive input."""
    try:
        name = input("\nCard name: ").strip()
        if not name:
            print("Card name cannot be empty.")
            return False

        description = input("Card description (optional, press Enter to skip): ").strip()
        card = client.create_card(
            list_id=list_id,
            name=name,
            description=description if description else None,
        )
        print(f"Card '{card['name']}' created successfully.")
        return True
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return False
    except TrelloAPIError as e:
        print(f"Failed to create card: {e}", file=sys.stderr)
        return False


def move_cards(client: TrelloClient, board_id: str) -> bool:
    """Handle moving cards between lists.

    Args:
        client: TrelloClient instance
        board_id: ID of the board

    Returns:
        True if cards were moved, False otherwise
    """
    lists = _get_board_lists(client, board_id)
    if lists is None:
        return False

    source_list = select_list(lists, "Select source list")
    if not source_list:
        return False

    cards = _get_list_cards(client, source_list["id"])
    if cards is None:
        return False

    selected_cards = select_cards(cards, "Select cards to move")
    if not selected_cards:
        print("No cards selected.")
        return False

    target_list = select_list(lists, "Select target list")
    if not target_list:
        return False

    if target_list["id"] == source_list["id"]:
        print("Source and target list are the same. No cards moved.")
        return False

    return _execute_card_moves(client, selected_cards, target_list)


def _get_list_cards(client: TrelloClient, list_id: str) -> list[dict] | None:
    """Get cards from a list with error handling."""
    try:
        return client.get_list_cards(list_id)
    except TrelloAPIError as e:
        print(f"Failed to get cards: {e}", file=sys.stderr)
        return None


def _execute_card_moves(
    client: TrelloClient, cards: list[dict], target_list: dict
) -> bool:
    """Execute card moves with error handling."""
    moved_count = 0
    for card in cards:
        try:
            client.move_card(card_id=card["id"], list_id=target_list["id"])
            moved_count += 1
        except TrelloAPIError as e:
            print(f"Failed to move '{card['name']}': {e}", file=sys.stderr)

    print(f"Moved {moved_count} card(s) to '{target_list['name']}'.")
    return moved_count > 0


def update_cards(client: TrelloClient, board_id: str) -> bool:
    """Handle updating card properties.

    Args:
        client: TrelloClient instance
        board_id: ID of the board

    Returns:
        True if cards were updated, False otherwise
    """
    lists = _get_board_lists(client, board_id)
    if lists is None:
        return False

    selected_list = select_list(lists, "Select a list")
    if not selected_list:
        return False

    cards = _get_list_cards(client, selected_list["id"])
    if cards is None:
        return False

    selected_cards = select_cards(cards, "Select cards to update")
    if not selected_cards:
        print("No cards selected.")
        return False

    update_choice = _show_update_menu()
    if update_choice == "0":
        return False

    return _execute_update(client, selected_cards, update_choice)


def _show_update_menu() -> str:
    """Show update options menu and get choice."""
    print("\nWhat would you like to update?")
    print("  1. Name")
    print("  2. Description")
    print("  3. Archive (close) cards")
    print("  0. Cancel")

    try:
        return input("\nEnter choice: ").strip()
    except (EOFError, KeyboardInterrupt):
        return "0"


def _execute_update(
    client: TrelloClient, cards: list[dict], update_choice: str
) -> bool:
    """Execute the selected update operation."""
    if update_choice == "1":
        return _update_card_names(client, cards)
    elif update_choice == "2":
        return _update_card_descriptions(client, cards)
    elif update_choice == "3":
        return _archive_cards(client, cards)
    return False


def _update_card_names(client: TrelloClient, cards: list[dict]) -> bool:
    """Update card names interactively."""
    updated_count = 0
    for card in cards:
        try:
            new_name = input(f"New name for '{card['name']}' (Enter to skip): ").strip()
            if new_name:
                client.update_card(card_id=card["id"], name=new_name)
                print(f"Updated: {new_name}")
                updated_count += 1
        except (EOFError, KeyboardInterrupt):
            break
        except TrelloAPIError as e:
            print(f"Failed to update '{card['name']}': {e}", file=sys.stderr)

    print(f"Updated {updated_count} card(s).")
    return updated_count > 0


def _update_card_descriptions(client: TrelloClient, cards: list[dict]) -> bool:
    """Update card descriptions."""
    try:
        new_desc = input("New description for all selected cards: ").strip()
    except (EOFError, KeyboardInterrupt):
        return False

    if not new_desc:
        print("Updated 0 card(s).")
        return False

    updated_count = 0
    for card in cards:
        try:
            client.update_card(card_id=card["id"], description=new_desc)
            updated_count += 1
        except TrelloAPIError as e:
            print(f"Failed to update '{card['name']}': {e}", file=sys.stderr)

    print(f"Updated {updated_count} card(s).")
    return updated_count > 0


def _archive_cards(client: TrelloClient, cards: list[dict]) -> bool:
    """Archive selected cards."""
    try:
        confirm = input(f"Archive {len(cards)} card(s)? (yes/no): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False

    if confirm not in ("yes", "y"):
        print("Updated 0 card(s).")
        return False

    updated_count = 0
    for card in cards:
        try:
            client.update_card(card_id=card["id"], closed=True)
            updated_count += 1
        except TrelloAPIError as e:
            print(f"Failed to archive '{card['name']}': {e}", file=sys.stderr)

    print(f"Updated {updated_count} card(s).")
    return updated_count > 0


def delete_cards(client: TrelloClient, board_id: str) -> bool:
    """Handle deleting cards with confirmation.

    Args:
        client: TrelloClient instance
        board_id: ID of the board

    Returns:
        True if cards were deleted, False otherwise
    """
    lists = _get_board_lists(client, board_id)
    if lists is None:
        return False

    selected_list = select_list(lists, "Select a list")
    if not selected_list:
        return False

    cards = _get_list_cards(client, selected_list["id"])
    if cards is None:
        return False

    selected_cards = select_cards(cards, "Select cards to delete")
    if not selected_cards:
        print("No cards selected.")
        return False

    if not _confirm_delete(selected_cards):
        print("Deletion cancelled.")
        return False

    return _execute_deletions(client, selected_cards)


def _confirm_delete(cards: list[dict]) -> bool:
    """Confirm deletion with user."""
    print("\nCards to delete:")
    for card in cards:
        print(f"  - {card['name']}")

    try:
        confirm = input(
            f"\nDelete {len(cards)} card(s)? This cannot be undone. (yes/no): "
        ).strip().lower()
        return confirm in ("yes", "y")
    except (EOFError, KeyboardInterrupt):
        return False


def _execute_deletions(client: TrelloClient, cards: list[dict]) -> bool:
    """Execute card deletions."""
    deleted_count = 0
    for card in cards:
        try:
            client.delete_card(card["id"])
            deleted_count += 1
        except TrelloAPIError as e:
            print(f"Failed to delete '{card['name']}': {e}", file=sys.stderr)

    print(f"Deleted {deleted_count} card(s).")
    return deleted_count > 0


def show_menu() -> str:
    """Display the bulk edit operations menu.

    Returns:
        User's menu choice
    """
    print("\n" + "=" * 40)
    print("Bulk Card Operations")
    print("=" * 40)
    print("  1. Add a new card")
    print("  2. Move cards between lists")
    print("  3. Update card properties")
    print("  4. Delete cards")
    print("  0. Exit edit mode")

    try:
        return input("\nSelect operation: ").strip()
    except (EOFError, KeyboardInterrupt):
        return "0"


def run_edit_session(client: TrelloClient, board_id: str | None) -> int:
    """Handle interactive bulk editing of a board.

    Args:
        client: TrelloClient instance
        board_id: Specific board ID to edit, or None for interactive selection

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    board = _resolve_board(client, board_id)
    if board is None:
        return 0 if board_id is None else 1

    resolved_id = board["id"]
    print(f"\nEditing board: {board.get('name', resolved_id)}")

    _run_menu_loop(client, resolved_id)
    return 0


def _resolve_board(client: TrelloClient, board_id: str | None) -> dict | None:
    """Resolve board from ID or interactive selection."""
    if board_id:
        try:
            return client.get_board(board_id)
        except TrelloAPIError as e:
            if e.status_code == 404:
                print("Board not found or you don't have access.", file=sys.stderr)
            else:
                print(f"Failed to get board: {e}", file=sys.stderr)
            return None

    board = select_board(client)
    if not board:
        print("No board selected.")
    return board


def _run_menu_loop(client: TrelloClient, board_id: str) -> None:
    """Run the edit menu loop."""
    handlers = {
        "1": add_card,
        "2": move_cards,
        "3": update_cards,
        "4": delete_cards,
    }

    while True:
        choice = show_menu()

        if choice == "0":
            print("Exiting edit mode.")
            break
        elif choice in handlers:
            handlers[choice](client, board_id)
        else:
            print("Invalid choice. Please select 0-4.")
