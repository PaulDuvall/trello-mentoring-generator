# Trello Career Planner

A command-line tool that generates a comprehensive Trello board for tech career planning. Creates a pre-populated board with lists and cards covering career goals, skills assessment, learning plans, networking strategies, and job search preparation.

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
- Creates a fully populated Trello board with 7 lists and 25+ cards
- Covers all aspects of tech career development
- Color-coded labels for prioritization and tracking
- Customizable board names
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

The generated board includes:

### Lists

1. **Career Goals** - Define your 1-year and 5-year vision
2. **Skills Assessment** - Inventory current skills and identify gaps
3. **Learning & Development** - Courses, certifications, and projects
4. **Networking** - Build connections and find mentors
5. **Job Search Preparation** - Resume, portfolio, and interview prep
6. **Weekly Actions** - Recurring tasks for consistent progress
7. **Completed** - Archive for completed items

### Labels

- **High Priority** (red) - Focus on these first
- **In Progress** (yellow) - Currently working on
- **Completed** (green) - Done
- **Learning** (blue) - Educational activities
- **Networking** (purple) - Relationship building
- **Long Term** (orange) - Future goals

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
│       ├── generator.py      # Board generation logic
│       └── template.py       # Career template definition
├── tests/                    # Unit tests (92 tests, 100% pass)
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
