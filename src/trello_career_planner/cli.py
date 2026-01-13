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
from . import edit


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="trello-career-planner",
        description="Generate a Trello board for tech career planning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_get_epilog(),
    )
    _add_arguments(parser)
    return parser


def _get_epilog() -> str:
    """Return CLI epilog with usage examples."""
    return """
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
"""


def _add_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all CLI arguments to parser."""
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--name", "-n", dest="board_name",
        help="Custom name for the generated board (default: 'Tech Career Planning')",
    )
    parser.add_argument(
        "--api-key", "-k", dest="api_key",
        help="Trello API key (can also use TRELLO_API_KEY env var)",
    )
    parser.add_argument(
        "--token", "-t", dest="token",
        help="Trello API token (can also use TRELLO_TOKEN env var)",
    )
    parser.add_argument(
        "--env-file", "-e", dest="env_file",
        help="Path to .env file with credentials",
    )
    parser.add_argument(
        "--verify-only", action="store_true",
        help="Only verify credentials without creating a board",
    )
    parser.add_argument(
        "--setup-help", action="store_true",
        help="Show detailed instructions for setting up Trello credentials",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show detailed progress during board creation",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be created without making API calls",
    )
    parser.add_argument(
        "--delete", "-d", action="store_true",
        help="Delete a Trello board (interactive selection)",
    )
    parser.add_argument(
        "--board-id", dest="board_id",
        help="Board ID to delete or edit (skips interactive selection)",
    )
    parser.add_argument(
        "--yes", "-y", action="store_true",
        help="Skip confirmation prompt (use with --delete)",
    )
    parser.add_argument(
        "--edit", action="store_true",
        help="Interactive bulk editing mode for existing boards",
    )


def show_dry_run() -> None:
    """Display what would be created in a dry run."""
    template = get_tech_career_template()
    print(f"\nBoard: {template.name}")
    print(f"Description: {template.description[:80]}...")
    _print_labels(template)
    _print_lists(template)
    total_cards = sum(len(lst.cards) for lst in template.lists)
    print(f"\nTotal: {len(template.lists)} lists, {total_cards} cards")


def _print_labels(template) -> None:
    """Print template labels."""
    print(f"\nLabels ({len(template.labels)}):")
    for label in template.labels:
        print(f"  - {label.name} ({label.color})")


def _print_lists(template) -> None:
    """Print template lists and cards."""
    print(f"\nLists ({len(template.lists)}):")
    for lst in template.lists:
        print(f"  {lst.name} ({len(lst.cards)} cards)")
        for card in lst.cards:
            labels_str = f" [{', '.join(card.labels)}]" if card.labels else ""
            print(f"    - {card.name}{labels_str}")


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

    return _get_board_selection(boards, "delete")


def _get_board_selection(boards: list[dict], action: str) -> str | None:
    """Get board selection from user input."""
    while True:
        try:
            choice = input(f"\nSelect a board number to {action}: ").strip()
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
        prompt = f"\nAre you sure you want to delete '{board_name}'? "
        prompt += "This cannot be undone. (yes/no): "
        response = input(prompt)
        return response.strip().lower() in ("yes", "y")
    except (EOFError, KeyboardInterrupt):
        return False


def delete_board_command(
    client: TrelloClient, board_id: str | None, skip_confirm: bool
) -> int:
    """Handle the board deletion command.

    Args:
        client: TrelloClient instance
        board_id: Specific board ID to delete, or None for interactive selection
        skip_confirm: Skip confirmation prompt if True

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        selected_id, board_name = _resolve_deletion_target(client, board_id)
        if not selected_id:
            print("Deletion cancelled.")
            return 0

        if not skip_confirm and not confirm_deletion(board_name):
            print("Deletion cancelled.")
            return 0

        client.delete_board(selected_id)
        print(f"Board '{board_name}' deleted successfully.")
        return 0

    except TrelloAPIError as e:
        return _handle_delete_error(e)


def _resolve_deletion_target(
    client: TrelloClient, board_id: str | None
) -> tuple[str | None, str]:
    """Resolve board ID and name for deletion."""
    if board_id:
        board = client.get_board(board_id)
        return board_id, board.get("name", board_id)

    selected_id = select_board_for_deletion(client)
    if not selected_id:
        return None, ""

    board = client.get_board(selected_id)
    return selected_id, board.get("name", selected_id)


def _handle_delete_error(e: TrelloAPIError) -> int:
    """Handle deletion error and return exit code."""
    if e.status_code == 404:
        msg = "Board not found. It may have already been deleted or you don't have access."
        print(msg, file=sys.stderr)
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
        name = member.get("fullName", member.get("username"))
        print(f"Credentials valid! Authenticated as: {name}")
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

    # Handle early-exit commands
    if parsed_args.setup_help:
        print(get_credentials_help())
        return 0

    if parsed_args.dry_run:
        show_dry_run()
        return 0

    # Load and validate credentials
    client = _create_client(parsed_args)
    if client is None:
        return 1

    # Dispatch to command handlers
    if parsed_args.verify_only:
        return verify_credentials_only(client)

    if parsed_args.delete:
        return delete_board_command(client, parsed_args.board_id, parsed_args.yes)

    if parsed_args.edit:
        return edit.run_edit_session(client, parsed_args.board_id)

    return _create_board(client, parsed_args)


def _create_client(parsed_args) -> TrelloClient | None:
    """Create authenticated Trello client."""
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
        return None

    return TrelloClient(
        api_key=credentials.api_key,
        token=credentials.token,
    )


def _create_board(client: TrelloClient, parsed_args) -> int:
    """Create a new career planning board."""
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

        _print_success(result)
        return 0

    except TrelloAPIError as e:
        print(f"Trello API error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return 130


def _print_success(result) -> None:
    """Print board creation success message."""
    print()
    print("Board created successfully!")
    print(f"  Name: {result.board_name}")
    print(f"  URL: {result.board_url}")
    print(f"  Lists: {result.lists_created}")
    print(f"  Cards: {result.cards_created}")
    print(f"  Labels: {result.labels_created}")


if __name__ == "__main__":
    sys.exit(main())
