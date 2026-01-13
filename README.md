# Trello Career Planner

A command-line tool that generates a comprehensive Trello board for tech career planning using a hybrid weekly sprint workflow. Creates a pre-populated board with sprint-based task management alongside long-term career strategy and learning resources.

## Quick Start

```bash
# 1. Clone and enter directory
git clone <repository-url>
cd trello-mentoring-generator

# 2. Setup credentials (one-time)
cp .env.example .env
# Edit .env with your Trello API key and token

# 3. Run!
./run.sh
```

That's it! The script handles everything: virtual environment, dependencies, and execution.

## Features

- **Zero-friction setup** - Single command handles venv, dependencies, and execution
- **Hybrid weekly sprint workflow** - Sprint columns for weekly execution + reference lists for strategy
- Creates a fully populated Trello board with 9 lists and 22 cards
- Color-coded labels for prioritization and tracking
- Customizable board names
- **Board deletion** - Interactive selection with confirmation safeguards
- **Bulk editing** - Interactive mode to add, move, update, and delete cards
- Dry-run mode to preview without creating
- Credential verification

## Getting Trello API Credentials

1. **Get your API Key:**
   - Go to https://trello.com/app-key
   - Log in to your Trello account
   - Copy the API key shown on the page

2. **Generate a Token:**
   - On the same page, click "Generate a Token"
   - Authorize the application
   - Copy the token

3. **Create .env file:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your credentials:
   ```
   TRELLO_API_KEY=your_32_character_api_key
   TRELLO_TOKEN=your_64_character_token
   ```

## Usage

### Using run.sh (Recommended)

```bash
# Create a board (handles everything automatically)
./run.sh

# Custom board name
./run.sh --name "My Career Plan 2025"

# Preview what will be created (no credentials needed)
./run.sh --dry-run

# Verbose output
./run.sh --verbose

# Verify credentials
./run.sh --verify-only

# Delete a board (interactive selection)
./run.sh --delete

# Delete specific board by ID
./run.sh --delete --board-id BOARD_ID

# Delete without confirmation prompt (use with caution)
./run.sh --delete --board-id BOARD_ID --yes

# Edit an existing board (interactive mode)
./run.sh --edit

# Edit a specific board by ID
./run.sh --edit --board-id BOARD_ID

# Show setup help
./run.sh --setup-help

# Show all options
./run.sh --help
```

### Using Make (Development)

```bash
make help          # Show all commands
make install       # Setup venv and deps
make test          # Run tests
make test-cov      # Run tests with coverage
make lint          # Run linters
make format        # Auto-format code
make dry-run       # Preview board
make clean         # Remove artifacts
```

### Direct CLI (Advanced)

If you prefer to manage your own environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
trello-career-planner --help
deactivate
```

## Board Structure

The generated board uses a hybrid weekly sprint workflow:

### Sprint Workflow Lists

1. **Sprint Backlog** - Tasks ready to be pulled into weekly sprints
2. **This Week** - Current week's focused tasks
3. **In Progress** - Active work (limit 2-3 for focus)
4. **Blocked / Review** - Items waiting on dependencies or feedback
5. **Done This Week** - Completed this sprint cycle

### Tracking & Reference Lists

6. **Weekly Metrics** - Activity tracker for daily habits, learning, coding, job search, networking
7. **Career Goals & Strategy** - Long-term vision, target roles, skills inventory
8. **Learning Resources** - Courses, books, certifications, interview prep
9. **Completed** - Archive for historical tracking

### Labels

- **High Priority** (red) - Focus on these first
- **Quick Win** (green) - Fast tasks for momentum
- **Learning** (blue) - Educational activities
- **Networking** (purple) - Relationship building
- **Career Goal** (orange) - Strategic planning items
- **Blocked** (yellow) - Items with dependencies

## Bulk Edit Mode

The `--edit` flag provides interactive bulk editing for existing boards:

```bash
./run.sh --edit
```

### Available Operations

1. **Add a new card** - Create cards in any list with name and optional description
2. **Move cards between lists** - Select multiple cards and move them to a different list
3. **Update card properties** - Rename cards, update descriptions, or archive cards
4. **Delete cards** - Remove cards with confirmation prompt

### How It Works

1. Select a board from your available Trello boards
2. Choose an operation from the menu
3. Follow the interactive prompts to select lists/cards
4. Confirm destructive actions (delete/archive)
5. Repeat or exit when done

### Example Session

```
Your Trello boards:
  1. Tech Career Planning
  2. Project Ideas
  0. Cancel

Select a board number to edit: 1

Editing board: Tech Career Planning

========================================
Bulk Card Operations
========================================
  1. Add a new card
  2. Move cards between lists
  3. Update card properties
  4. Delete cards
  0. Exit edit mode

Select operation: 2

Select source list:
  1. Sprint Backlog
  2. This Week
  ...
```

## Project Structure

```
trello-mentoring-generator/
├── run.sh                    # Main entry point (recommended)
├── Makefile                  # Development commands
├── src/
│   └── trello_career_planner/
│       ├── __init__.py
│       ├── api_client.py     # Trello REST API client
│       ├── cli.py            # Command-line interface
│       ├── credentials.py    # Credential management
│       ├── edit.py           # Bulk edit functionality
│       ├── generator.py      # Board generation logic
│       └── template.py       # Career template definition
├── tests/                    # Unit tests (182 tests, 100% pass)
├── .env.example              # Credential template
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

## Development

```bash
# Full test suite
make test

# With coverage report
make test-cov

# Lint and format
make lint
make format

# Clean build artifacts
make clean
```

## API Reference

### TrelloClient

```python
from trello_career_planner.api_client import TrelloClient

client = TrelloClient(api_key="...", token="...")
client.verify_credentials()
board = client.create_board(name="My Board")
```

### BoardGenerator

```python
from trello_career_planner.generator import create_career_board
from trello_career_planner.api_client import TrelloClient

client = TrelloClient(api_key="...", token="...")
result = create_career_board(client, board_name="My Career Plan")
print(f"Board URL: {result.board_url}")
```

## Troubleshooting

### "No .env file found"

Create the file with your credentials:
```bash
cp .env.example .env
# Edit .env with your API key and token
```

### "API key not found" / "Token not found"

Ensure your `.env` file contains both values:
```
TRELLO_API_KEY=your_api_key_here
TRELLO_TOKEN=your_token_here
```

### "Invalid token"

Your token may have expired. Generate a new one at https://trello.com/app-key

### "Rate limit exceeded"

Trello has API rate limits. Wait a few minutes and try again.

### Permission warning on .env

For security, restrict access to your credentials:
```bash
chmod 600 .env
```

## Security

- Never commit your `.env` file (it's in `.gitignore`)
- API credentials are only read from environment variables or `.env` file
- Credentials are never logged or displayed
- The `.env` file should have restricted permissions (`chmod 600`)

## License

MIT License
