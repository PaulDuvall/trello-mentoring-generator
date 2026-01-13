"""Board generator that creates Trello boards from templates."""

from dataclasses import dataclass, field

from .api_client import TrelloClient, TrelloAPIError
from .template import BoardTemplate, get_tech_career_template


@dataclass
class GeneratedBoard:
    """Result of board generation."""

    board_id: str
    board_url: str
    board_name: str
    lists_created: int
    cards_created: int
    labels_created: int


@dataclass
class GenerationProgress:
    """Tracks progress during board generation."""

    total_lists: int = 0
    total_cards: int = 0
    lists_created: int = 0
    cards_created: int = 0
    labels_created: int = 0
    current_step: str = ""
    errors: list[str] = field(default_factory=list)


class BoardGenerator:
    """Generates Trello boards from templates."""

    def __init__(self, client: TrelloClient):
        """Initialize the board generator.

        Args:
            client: Authenticated Trello API client
        """
        self.client = client
        self.progress = GenerationProgress()
        self._label_map: dict[str, str] = {}

    def generate(
        self,
        template: BoardTemplate | None = None,
        board_name: str | None = None,
        progress_callback: callable | None = None,
    ) -> GeneratedBoard:
        """Generate a Trello board from a template.

        Args:
            template: Board template to use (defaults to tech career template)
            board_name: Override the board name from template
            progress_callback: Optional callback for progress updates

        Returns:
            GeneratedBoard with details of the created board

        Raises:
            TrelloAPIError: If board creation fails
        """
        if template is None:
            template = get_tech_career_template()

        name = board_name or template.name
        self.progress = GenerationProgress()
        self.progress.total_lists = len(template.lists)
        self.progress.total_cards = sum(len(lst.cards) for lst in template.lists)

        self._label_map = {}

        self._update_progress("Creating board...", progress_callback)
        board = self.client.create_board(
            name=name,
            description=template.description,
            default_lists=False,
        )
        board_id = board["id"]
        board_url = board.get("url", f"https://trello.com/b/{board_id}")

        self._update_progress("Creating labels...", progress_callback)
        self._create_labels(board_id, template, progress_callback)

        self._update_progress("Creating lists and cards...", progress_callback)
        self._create_lists_and_cards(board_id, template, progress_callback)

        self._update_progress("Board generation complete!", progress_callback)

        return GeneratedBoard(
            board_id=board_id,
            board_url=board_url,
            board_name=name,
            lists_created=self.progress.lists_created,
            cards_created=self.progress.cards_created,
            labels_created=self.progress.labels_created,
        )

    def _update_progress(
        self,
        step: str,
        callback: callable | None = None,
    ) -> None:
        """Update progress and optionally call callback.

        Args:
            step: Current step description
            callback: Optional progress callback
        """
        self.progress.current_step = step
        if callback:
            callback(self.progress)

    def _create_labels(
        self,
        board_id: str,
        template: BoardTemplate,
        progress_callback: callable | None = None,
    ) -> None:
        """Create labels on the board.

        Args:
            board_id: ID of the board
            template: Board template with label definitions
            progress_callback: Optional progress callback
        """
        for label_template in template.labels:
            try:
                label = self.client.create_label(
                    board_id=board_id,
                    name=label_template.name,
                    color=label_template.color,
                )
                self._label_map[label_template.name] = label["id"]
                self.progress.labels_created += 1
                self._update_progress(
                    f"Created label: {label_template.name}",
                    progress_callback,
                )
            except TrelloAPIError as e:
                self.progress.errors.append(f"Failed to create label {label_template.name}: {e}")

    def _create_lists_and_cards(
        self,
        board_id: str,
        template: BoardTemplate,
        progress_callback: callable | None = None,
    ) -> None:
        """Create lists and their cards on the board.

        Args:
            board_id: ID of the board
            template: Board template with list and card definitions
            progress_callback: Optional progress callback
        """
        for list_template in template.lists:
            try:
                trello_list = self.client.create_list(
                    board_id=board_id,
                    name=list_template.name,
                )
                list_id = trello_list["id"]
                self.progress.lists_created += 1
                self._update_progress(
                    f"Created list: {list_template.name}",
                    progress_callback,
                )

                for card_template in list_template.cards:
                    self._create_card(list_id, card_template, progress_callback)

            except TrelloAPIError as e:
                self.progress.errors.append(f"Failed to create list {list_template.name}: {e}")

    def _create_card(
        self,
        list_id: str,
        card_template,
        progress_callback: callable | None = None,
    ) -> None:
        """Create a card in a list.

        Args:
            list_id: ID of the list
            card_template: Card template with card details
            progress_callback: Optional progress callback
        """
        try:
            label_ids = [
                self._label_map[label_name]
                for label_name in card_template.labels
                if label_name in self._label_map
            ]

            self.client.create_card(
                list_id=list_id,
                name=card_template.name,
                description=card_template.description,
                labels=label_ids if label_ids else None,
            )
            self.progress.cards_created += 1
            self._update_progress(
                f"Created card: {card_template.name}",
                progress_callback,
            )
        except TrelloAPIError as e:
            self.progress.errors.append(f"Failed to create card {card_template.name}: {e}")


def create_career_board(
    client: TrelloClient,
    board_name: str | None = None,
    verbose: bool = False,
) -> GeneratedBoard:
    """Convenience function to create a tech career planning board.

    Args:
        client: Authenticated Trello API client
        board_name: Optional custom board name
        verbose: Whether to print progress updates

    Returns:
        GeneratedBoard with details of the created board
    """

    def progress_printer(progress: GenerationProgress) -> None:
        if verbose:
            print(f"  {progress.current_step}")

    generator = BoardGenerator(client)
    return generator.generate(
        board_name=board_name,
        progress_callback=progress_printer if verbose else None,
    )
