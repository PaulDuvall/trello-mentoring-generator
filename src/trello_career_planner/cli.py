"""Command-line interface for Trello Career Planner."""

import argparse
import sys

from . import __version__
from .api_client import TrelloClient, TrelloAPIError
from .credentials import (
    CredentialError,
    load_credentials,
    validate_credentials,
    get_credentials_help,
)
from .generator import create_career_board
from .template import get_tech_career_template


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="trello-career-planner",
        description="Generate a Trello board for tech career planning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a board using environment variables for credentials
  trello-career-planner

  # Create a board with a custom name
  trello-career-planner --name "My Career Plan 2025"

  # Create a board with explicit credentials
  trello-career-planner --api-key YOUR_KEY --token YOUR_TOKEN

  # Verify credentials without creating a board
  trello-career-planner --verify-only

  # Show setup help
  trello-career-planner --setup-help
""",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "--name",
        "-n",
        dest="board_name",
        help="Custom name for the generated board (default: 'Tech Career Planning')",
    )

    parser.add_argument(
        "--api-key",
        "-k",
        dest="api_key",
        help="Trello API key (can also use TRELLO_API_KEY env var)",
    )

    parser.add_argument(
        "--token",
        "-t",
        dest="token",
        help="Trello API token (can also use TRELLO_TOKEN env var)",
    )

    parser.add_argument(
        "--env-file",
        "-e",
        dest="env_file",
        help="Path to .env file with credentials",
    )

    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify credentials without creating a board",
    )

    parser.add_argument(
        "--setup-help",
        action="store_true",
        help="Show detailed instructions for setting up Trello credentials",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed progress during board creation",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without making API calls",
    )

    parser.add_argument(
        "--delete",
        "-d",
        action="store_true",
        help="Delete a Trello board (interactive selection)",
    )

    parser.add_argument(
        "--board-id",
        dest="board_id",
        help="Board ID to delete (use with --delete to skip interactive selection)",
    )

    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt (use with --delete)",
    )

    parser.add_argument(
        "--edit",
        action="store_true",
        help="Interactive bulk editing mode for existing boards",
    )

    return parser


def show_dry_run() -> None:
    """Display what would be created in a dry run."""
    template = get_tech_career_template()
    print(f"\nBoard: {template.name}")
    print(f"Description: {template.description[:80]}...")
    print(f"\nLabels ({len(template.labels)}):")
    for label in template.labels:
        print(f"  - {label.name} ({label.color})")
    print(f"\nLists ({len(template.lists)}):")
    for lst in template.lists:
        print(f"  {lst.name} ({len(lst.cards)} cards)")
        for card in lst.cards:
            labels_str = f" [{', '.join(card.labels)}]" if card.labels else ""
            print(f"    - {card.name}{labels_str}")
    total_cards = sum(len(lst.cards) for lst in template.lists)
    print(f"\nTotal: {len(template.lists)} lists, {total_cards} cards")


def select_board_for_deletion(client: TrelloClient) -> str | None:
    """Display boards and let user select one for deletion.

    Args:
        client: TrelloClient instance

    Returns:
        Board ID if selected, None if cancelled
    """
    boards = client.list_boards(filter_type="open")
    if not boards:
        print("No open boards found.")
        return None

    print("\nYour Trello boards:")
    for i, board in enumerate(boards, 1):
        print(f"  {i}. {board['name']}")
    print("  0. Cancel")

    while True:
        try:
            choice = input("\nSelect a board number to delete: ").strip()
            if choice == "0":
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(boards):
                return boards[idx]["id"]
            print(f"Please enter a number between 0 and {len(boards)}")
        except ValueError:
            print("Please enter a valid number")
        except (EOFError, KeyboardInterrupt):
            return None


def confirm_deletion(board_name: str) -> bool:
    """Ask user to confirm board deletion.

    Args:
        board_name: Name of the board to delete

    Returns:
        True if confirmed, False otherwise
    """
    try:
        response = input(f"\nAre you sure you want to delete '{board_name}'? This cannot be undone. (yes/no): ")
        return response.strip().lower() in ("yes", "y")
    except (EOFError, KeyboardInterrupt):
        return False


def delete_board_command(client: TrelloClient, board_id: str | None, skip_confirm: bool) -> int:
    """Handle the board deletion command.

    Args:
        client: TrelloClient instance
        board_id: Specific board ID to delete, or None for interactive selection
        skip_confirm: Skip confirmation prompt if True

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        if board_id:
            # Verify the board exists and user owns it
            board = client.get_board(board_id)
            board_name = board.get("name", board_id)
            selected_id = board_id
        else:
            selected_id = select_board_for_deletion(client)
            if not selected_id:
                print("Deletion cancelled.")
                return 0
            board = client.get_board(selected_id)
            board_name = board.get("name", selected_id)

        if not skip_confirm and not confirm_deletion(board_name):
            print("Deletion cancelled.")
            return 0

        client.delete_board(selected_id)
        print(f"Board '{board_name}' deleted successfully.")
        return 0

    except TrelloAPIError as e:
        if e.status_code == 404:
            print("Board not found. It may have already been deleted or you don't have access.", file=sys.stderr)
        else:
            print(f"Failed to delete board: {e}", file=sys.stderr)
        return 1


def select_board_for_editing(client: TrelloClient) -> dict | None:
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

    print("\nYour Trello boards:")
    for i, board in enumerate(boards, 1):
        print(f"  {i}. {board['name']}")
    print("  0. Cancel")

    while True:
        try:
            choice = input("\nSelect a board number to edit: ").strip()
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


def select_list_from_board(lists: list[dict], prompt: str = "Select a list") -> dict | None:
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

    while True:
        try:
            choice = input("\nEnter list number: ").strip()
            if choice == "0":
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(lists):
                return lists[idx]
            print(f"Please enter a number between 0 and {len(lists)}")
        except ValueError:
            print("Please enter a valid number")
        except (EOFError, KeyboardInterrupt):
            return None


def select_cards_from_list(cards: list[dict], prompt: str = "Select cards") -> list[dict]:
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

    print(f"\n{prompt}:")
    for i, card in enumerate(cards, 1):
        print(f"  {i}. {card['name']}")
    print("  0. Cancel / Done selecting")

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


def handle_add_card(client: TrelloClient, board_id: str) -> bool:
    """Handle adding a new card to a list.

    Args:
        client: TrelloClient instance
        board_id: ID of the board

    Returns:
        True if card was added, False otherwise
    """
    try:
        lists = client.get_board_lists(board_id)
    except TrelloAPIError as e:
        print(f"Failed to get lists: {e}", file=sys.stderr)
        return False

    selected_list = select_list_from_board(lists, "Select a list to add card to")
    if not selected_list:
        return False

    try:
        name = input("\nCard name: ").strip()
        if not name:
            print("Card name cannot be empty.")
            return False

        description = input("Card description (optional, press Enter to skip): ").strip()

        card = client.create_card(
            list_id=selected_list["id"],
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


def handle_move_cards(client: TrelloClient, board_id: str) -> bool:
    """Handle moving cards between lists.

    Args:
        client: TrelloClient instance
        board_id: ID of the board

    Returns:
        True if cards were moved, False otherwise
    """
    try:
        lists = client.get_board_lists(board_id)
    except TrelloAPIError as e:
        print(f"Failed to get lists: {e}", file=sys.stderr)
        return False

    source_list = select_list_from_board(lists, "Select source list")
    if not source_list:
        return False

    try:
        cards = client.get_list_cards(source_list["id"])
    except TrelloAPIError as e:
        print(f"Failed to get cards: {e}", file=sys.stderr)
        return False

    selected_cards = select_cards_from_list(cards, "Select cards to move")
    if not selected_cards:
        print("No cards selected.")
        return False

    target_list = select_list_from_board(lists, "Select target list")
    if not target_list:
        return False

    if target_list["id"] == source_list["id"]:
        print("Source and target list are the same. No cards moved.")
        return False

    moved_count = 0
    for card in selected_cards:
        try:
            client.move_card(card_id=card["id"], list_id=target_list["id"])
            moved_count += 1
        except TrelloAPIError as e:
            print(f"Failed to move '{card['name']}': {e}", file=sys.stderr)

    print(f"Moved {moved_count} card(s) to '{target_list['name']}'.")
    return moved_count > 0


def handle_update_cards(client: TrelloClient, board_id: str) -> bool:
    """Handle updating card properties.

    Args:
        client: TrelloClient instance
        board_id: ID of the board

    Returns:
        True if cards were updated, False otherwise
    """
    try:
        lists = client.get_board_lists(board_id)
    except TrelloAPIError as e:
        print(f"Failed to get lists: {e}", file=sys.stderr)
        return False

    selected_list = select_list_from_board(lists, "Select a list")
    if not selected_list:
        return False

    try:
        cards = client.get_list_cards(selected_list["id"])
    except TrelloAPIError as e:
        print(f"Failed to get cards: {e}", file=sys.stderr)
        return False

    selected_cards = select_cards_from_list(cards, "Select cards to update")
    if not selected_cards:
        print("No cards selected.")
        return False

    print("\nWhat would you like to update?")
    print("  1. Name")
    print("  2. Description")
    print("  3. Archive (close) cards")
    print("  0. Cancel")

    try:
        update_choice = input("\nEnter choice: ").strip()
    except (EOFError, KeyboardInterrupt):
        return False

    if update_choice == "0":
        return False

    updated_count = 0

    if update_choice == "1":
        for card in selected_cards:
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

    elif update_choice == "2":
        try:
            new_desc = input("New description for all selected cards: ").strip()
        except (EOFError, KeyboardInterrupt):
            return False
        if new_desc:
            for card in selected_cards:
                try:
                    client.update_card(card_id=card["id"], description=new_desc)
                    updated_count += 1
                except TrelloAPIError as e:
                    print(f"Failed to update '{card['name']}': {e}", file=sys.stderr)

    elif update_choice == "3":
        try:
            confirm = input(f"Archive {len(selected_cards)} card(s)? (yes/no): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        if confirm in ("yes", "y"):
            for card in selected_cards:
                try:
                    client.update_card(card_id=card["id"], closed=True)
                    updated_count += 1
                except TrelloAPIError as e:
                    print(f"Failed to archive '{card['name']}': {e}", file=sys.stderr)

    print(f"Updated {updated_count} card(s).")
    return updated_count > 0


def handle_delete_cards(client: TrelloClient, board_id: str) -> bool:
    """Handle deleting cards with confirmation.

    Args:
        client: TrelloClient instance
        board_id: ID of the board

    Returns:
        True if cards were deleted, False otherwise
    """
    try:
        lists = client.get_board_lists(board_id)
    except TrelloAPIError as e:
        print(f"Failed to get lists: {e}", file=sys.stderr)
        return False

    selected_list = select_list_from_board(lists, "Select a list")
    if not selected_list:
        return False

    try:
        cards = client.get_list_cards(selected_list["id"])
    except TrelloAPIError as e:
        print(f"Failed to get cards: {e}", file=sys.stderr)
        return False

    selected_cards = select_cards_from_list(cards, "Select cards to delete")
    if not selected_cards:
        print("No cards selected.")
        return False

    print(f"\nCards to delete:")
    for card in selected_cards:
        print(f"  - {card['name']}")

    try:
        confirm = input(f"\nDelete {len(selected_cards)} card(s)? This cannot be undone. (yes/no): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False

    if confirm not in ("yes", "y"):
        print("Deletion cancelled.")
        return False

    deleted_count = 0
    for card in selected_cards:
        try:
            client.delete_card(card["id"])
            deleted_count += 1
        except TrelloAPIError as e:
            print(f"Failed to delete '{card['name']}': {e}", file=sys.stderr)

    print(f"Deleted {deleted_count} card(s).")
    return deleted_count > 0


def show_edit_menu() -> str:
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
        choice = input("\nSelect operation: ").strip()
        return choice
    except (EOFError, KeyboardInterrupt):
        return "0"


def edit_board_command(client: TrelloClient, board_id: str | None) -> int:
    """Handle interactive bulk editing of a board.

    Args:
        client: TrelloClient instance
        board_id: Specific board ID to edit, or None for interactive selection

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    if board_id:
        try:
            board = client.get_board(board_id)
        except TrelloAPIError as e:
            if e.status_code == 404:
                print("Board not found or you don't have access.", file=sys.stderr)
            else:
                print(f"Failed to get board: {e}", file=sys.stderr)
            return 1
    else:
        board = select_board_for_editing(client)
        if not board:
            print("No board selected.")
            return 0

    board_id = board["id"]
    board_name = board.get("name", board_id)
    print(f"\nEditing board: {board_name}")

    while True:
        choice = show_edit_menu()

        if choice == "0":
            print("Exiting edit mode.")
            break
        elif choice == "1":
            handle_add_card(client, board_id)
        elif choice == "2":
            handle_move_cards(client, board_id)
        elif choice == "3":
            handle_update_cards(client, board_id)
        elif choice == "4":
            handle_delete_cards(client, board_id)
        else:
            print("Invalid choice. Please select 0-4.")

    return 0


def verify_credentials_only(client: TrelloClient) -> int:
    """Verify credentials and return exit code.

    Args:
        client: TrelloClient instance

    Returns:
        0 if credentials are valid, 1 otherwise
    """
    try:
        member = client.verify_credentials()
        print(f"Credentials valid! Authenticated as: {member.get('fullName', member.get('username'))}")
        return 0
    except TrelloAPIError as e:
        print(f"Credential verification failed: {e}", file=sys.stderr)
        return 1


def main(args: list[str] | None = None) -> int:
    """Main entry point for the CLI.

    Args:
        args: Command line arguments (uses sys.argv if None)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    if parsed_args.setup_help:
        print(get_credentials_help())
        return 0

    if parsed_args.dry_run:
        show_dry_run()
        return 0

    try:
        credentials = load_credentials(
            api_key=parsed_args.api_key,
            token=parsed_args.token,
            env_file=parsed_args.env_file,
        )
        validate_credentials(credentials)
    except CredentialError as e:
        print(f"Credential error: {e}", file=sys.stderr)
        print("\nRun with --setup-help for instructions on setting up credentials.")
        return 1

    client = TrelloClient(
        api_key=credentials.api_key,
        token=credentials.token,
    )

    if parsed_args.verify_only:
        return verify_credentials_only(client)

    if parsed_args.delete:
        return delete_board_command(client, parsed_args.board_id, parsed_args.yes)

    if parsed_args.edit:
        return edit_board_command(client, parsed_args.board_id)

    try:
        if parsed_args.verbose:
            print("Verifying credentials...")

        client.verify_credentials()

        if parsed_args.verbose:
            print("Creating your Tech Career Planning board...")
            print()

        result = create_career_board(
            client=client,
            board_name=parsed_args.board_name,
            verbose=parsed_args.verbose,
        )

        print()
        print("Board created successfully!")
        print(f"  Name: {result.board_name}")
        print(f"  URL: {result.board_url}")
        print(f"  Lists: {result.lists_created}")
        print(f"  Cards: {result.cards_created}")
        print(f"  Labels: {result.labels_created}")
        return 0

    except TrelloAPIError as e:
        print(f"Trello API error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
