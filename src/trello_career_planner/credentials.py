"""Credential setup and validation for Trello API."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class CredentialError(Exception):
    """Exception raised for credential-related errors."""

    pass


@dataclass
class TrelloCredentials:
    """Container for Trello API credentials."""

    api_key: str
    token: str

    def __post_init__(self):
        """Validate credentials are not empty."""
        if not self.api_key:
            raise CredentialError("API key cannot be empty")
        if not self.token:
            raise CredentialError("Token cannot be empty")


def load_credentials(
    api_key: str | None = None,
    token: str | None = None,
    env_file: str | Path | None = None,
) -> TrelloCredentials:
    """Load Trello credentials from arguments, environment, or .env file.

    Credential sources are checked in order of priority:
    1. Explicitly provided arguments
    2. Environment variables
    3. .env file

    Args:
        api_key: Trello API key (optional, will use env if not provided)
        token: Trello API token (optional, will use env if not provided)
        env_file: Path to .env file (optional)

    Returns:
        TrelloCredentials with validated API key and token

    Raises:
        CredentialError: If credentials cannot be found or are invalid
    """
    if env_file:
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_path)
        else:
            raise CredentialError(f"Environment file not found: {env_file}")
    else:
        load_dotenv()

    resolved_api_key = api_key or os.getenv("TRELLO_API_KEY")
    resolved_token = token or os.getenv("TRELLO_TOKEN")

    if not resolved_api_key:
        raise CredentialError(
            "Trello API key not found. Set TRELLO_API_KEY environment variable "
            "or provide via --api-key argument. "
            "Get your API key at: https://trello.com/app-key"
        )

    if not resolved_token:
        raise CredentialError(
            "Trello token not found. Set TRELLO_TOKEN environment variable "
            "or provide via --token argument. "
            "Generate a token at: https://trello.com/app-key (after getting your API key)"
        )

    return TrelloCredentials(api_key=resolved_api_key, token=resolved_token)


def validate_credentials(credentials: TrelloCredentials) -> bool:
    """Validate that credentials have the expected format.

    Args:
        credentials: TrelloCredentials to validate

    Returns:
        True if credentials appear valid

    Raises:
        CredentialError: If credentials have invalid format
    """
    if len(credentials.api_key) < 16:
        raise CredentialError(
            "API key appears too short. Trello API keys are typically 32 characters."
        )

    if len(credentials.token) < 32:
        raise CredentialError(
            "Token appears too short. Trello tokens are typically 64 characters."
        )

    return True


def get_credentials_help() -> str:
    """Get help text for setting up Trello credentials.

    Returns:
        Help text with instructions for obtaining credentials
    """
    return """
Trello API Credentials Setup
============================

To use this tool, you need a Trello API key and token.

Step 1: Get your API Key
------------------------
1. Go to https://trello.com/app-key
2. Log in to your Trello account if prompted
3. Copy the API key shown on the page

Step 2: Generate a Token
------------------------
1. On the same page (https://trello.com/app-key), click "Generate a Token"
2. Authorize the application
3. Copy the token shown

Step 3: Configure Credentials
-----------------------------
Option A: Environment variables
    export TRELLO_API_KEY=your_api_key_here
    export TRELLO_TOKEN=your_token_here

Option B: Create a .env file in your project directory
    TRELLO_API_KEY=your_api_key_here
    TRELLO_TOKEN=your_token_here

Option C: Pass directly via command line
    trello-career-planner --api-key YOUR_KEY --token YOUR_TOKEN

Security Note: Never commit your .env file or share your credentials publicly.
"""
