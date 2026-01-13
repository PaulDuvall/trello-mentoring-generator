"""Tests for the tech career template."""

import pytest

from trello_career_planner.template import (
    BoardTemplate,
    ListTemplate,
    CardTemplate,
    LabelTemplate,
    get_tech_career_template,
)


class TestDataClasses:
    """Tests for template data classes."""

    def test_card_template_defaults(self):
        """CardTemplate has sensible defaults."""
        card = CardTemplate(name="Test Card")
        assert card.name == "Test Card"
        assert card.description == ""
        assert card.labels == []

    def test_card_template_with_values(self):
        """CardTemplate accepts all values."""
        card = CardTemplate(
            name="Test Card",
            description="A description",
            labels=["label1", "label2"],
        )
        assert card.name == "Test Card"
        assert card.description == "A description"
        assert card.labels == ["label1", "label2"]

    def test_list_template_defaults(self):
        """ListTemplate has sensible defaults."""
        lst = ListTemplate(name="Test List")
        assert lst.name == "Test List"
        assert lst.cards == []

    def test_list_template_with_cards(self):
        """ListTemplate accepts cards."""
        cards = [CardTemplate(name="Card 1"), CardTemplate(name="Card 2")]
        lst = ListTemplate(name="Test List", cards=cards)
        assert len(lst.cards) == 2

    def test_label_template(self):
        """LabelTemplate stores name and color."""
        label = LabelTemplate(name="Priority", color="red")
        assert label.name == "Priority"
        assert label.color == "red"

    def test_board_template_defaults(self):
        """BoardTemplate has sensible defaults."""
        board = BoardTemplate(name="Test Board", description="A board")
        assert board.name == "Test Board"
        assert board.description == "A board"
        assert board.labels == []
        assert board.lists == []


class TestTechCareerTemplate:
    """Tests for the tech career template."""

    @pytest.fixture
    def template(self):
        """Get the tech career template."""
        return get_tech_career_template()

    def test_template_has_name(self, template):
        """Template has a board name."""
        assert template.name == "Tech Career Planning"

    def test_template_has_description(self, template):
        """Template has a description."""
        assert len(template.description) > 0
        assert "career" in template.description.lower()

    def test_template_has_labels(self, template):
        """Template defines labels."""
        assert len(template.labels) >= 4
        label_names = [l.name for l in template.labels]
        assert "High Priority" in label_names
        assert "Blocked" in label_names  # Sprint workflow label

    def test_labels_have_valid_colors(self, template):
        """All labels have valid Trello colors."""
        valid_colors = {
            "yellow", "purple", "blue", "red", "green",
            "orange", "black", "sky", "pink", "lime",
        }
        for label in template.labels:
            assert label.color in valid_colors, f"Invalid color: {label.color}"

    def test_template_has_lists(self, template):
        """Template has multiple lists."""
        assert len(template.lists) >= 5
        list_names = [l.name for l in template.lists]
        # Sprint workflow lists
        assert "Sprint Backlog" in list_names
        assert "This Week" in list_names
        assert "In Progress" in list_names
        # Reference lists
        assert "Career Goals & Strategy" in list_names
        assert "Learning Resources" in list_names

    def test_all_lists_have_cards(self, template):
        """Each list has at least one card."""
        for lst in template.lists:
            assert len(lst.cards) >= 1, f"List '{lst.name}' has no cards"

    def test_cards_have_descriptions(self, template):
        """Most cards have descriptions."""
        cards_with_desc = 0
        total_cards = 0
        for lst in template.lists:
            for card in lst.cards:
                total_cards += 1
                if card.description:
                    cards_with_desc += 1
        assert cards_with_desc / total_cards > 0.8

    def test_card_labels_reference_defined_labels(self, template):
        """Card labels reference labels defined on the board."""
        defined_labels = {l.name for l in template.labels}
        for lst in template.lists:
            for card in lst.cards:
                for label_name in card.labels:
                    assert label_name in defined_labels, (
                        f"Card '{card.name}' references undefined label '{label_name}'"
                    )

    def test_template_coverage(self, template):
        """Template covers key career planning areas via hybrid sprint workflow."""
        list_names = {l.name for l in template.lists}
        # Sprint workflow lists
        expected_sprint_lists = {
            "Sprint Backlog",
            "This Week",
            "In Progress",
            "Done This Week",
            "Completed",
        }
        for area in expected_sprint_lists:
            assert area in list_names, f"Missing expected sprint list: {area}"

        # Reference/strategy lists
        expected_reference_lists = {
            "Career Goals & Strategy",
            "Learning Resources",
        }
        for area in expected_reference_lists:
            assert area in list_names, f"Missing expected reference list: {area}"

    def test_sprint_workflow_structure(self, template):
        """Template has proper sprint workflow structure."""
        list_names = [l.name for l in template.lists]
        # Sprint lists should be in order at the beginning
        sprint_lists = ["Sprint Backlog", "This Week", "In Progress", "Blocked / Review", "Done This Week"]
        for sprint_list in sprint_lists:
            assert sprint_list in list_names, f"Missing sprint list: {sprint_list}"

    def test_blocked_label_exists(self, template):
        """Template has a Blocked label for sprint workflow."""
        label_names = [l.name for l in template.labels]
        assert "Blocked" in label_names

    def test_quick_win_label_exists(self, template):
        """Template has a Quick Win label for prioritization."""
        label_names = [l.name for l in template.labels]
        assert "Quick Win" in label_names

    def test_total_cards_reasonable(self, template):
        """Template has a reasonable number of cards."""
        total_cards = sum(len(lst.cards) for lst in template.lists)
        assert 20 <= total_cards <= 50, f"Unexpected card count: {total_cards}"
