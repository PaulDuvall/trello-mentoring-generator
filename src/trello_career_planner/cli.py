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
