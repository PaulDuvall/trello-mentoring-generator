#!/usr/bin/env bash
#
# run.sh - Single-command entry point for Trello Career Planner
#
# Usage: ./run.sh [options]
#   Options are passed directly to trello-career-planner CLI
#
# Examples:
#   ./run.sh                          # Create board using .env credentials
#   ./run.sh --name "My Career Plan"  # Create board with custom name
#   ./run.sh --dry-run                # Preview without creating
#   ./run.sh --help                   # Show all options
#

set -euo pipefail

# =============================================================================
# Constants
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
readonly VENV_DIR="${SCRIPT_DIR}/.venv"
readonly REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements.txt"
readonly ENV_FILE="${SCRIPT_DIR}/.env"
readonly MIN_PYTHON_VERSION="3.9"
readonly INSTALLED_MARKER="${VENV_DIR}/.installed"

# =============================================================================
# Color Output (with TTY detection)
# =============================================================================
if [[ -t 1 ]]; then
    RED=$'\033[0;31m'
    GREEN=$'\033[0;32m'
    YELLOW=$'\033[0;33m'
    BLUE=$'\033[0;34m'
    CYAN=$'\033[0;36m'
    BOLD=$'\033[1m'
    NC=$'\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    CYAN=''
    BOLD=''
    NC=''
fi
readonly RED GREEN YELLOW BLUE CYAN BOLD NC

# =============================================================================
# Output Functions (using printf for portability)
# =============================================================================
info() {
    printf '%s[*]%s %s\n' "$BLUE" "$NC" "$1"
}

success() {
    printf '%s[+]%s %s\n' "$GREEN" "$NC" "$1"
}

warn() {
    printf '%s[!]%s %s\n' "$YELLOW" "$NC" "$1" >&2
}

error() {
    printf '%s[x]%s %s\n' "$RED" "$NC" "$1" >&2
}

step() {
    printf '%s==>%s %s%s%s\n' "$CYAN" "$NC" "$BOLD" "$1" "$NC"
}

# =============================================================================
# Cleanup Handler
# =============================================================================
cleanup() {
    local exit_code=$?
    # Deactivate venv if it was activated
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        deactivate 2>/dev/null || true
    fi
    exit "$exit_code"
}

trap cleanup EXIT INT TERM

# =============================================================================
# Prerequisite Checks
# =============================================================================
check_python() {
    local python_cmd=""

    # Find Python 3
    if command -v python3 &>/dev/null; then
        python_cmd="python3"
    elif command -v python &>/dev/null; then
        python_cmd="python"
    else
        error "Python not found. Please install Python ${MIN_PYTHON_VERSION}+"
        printf '  macOS: brew install python3\n'
        printf '  Ubuntu: sudo apt install python3 python3-venv\n'
        return 1
    fi

    # Check version
    local version
    version=$("$python_cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

    if ! "$python_cmd" -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
        error "Python ${version} found, but ${MIN_PYTHON_VERSION}+ is required"
        return 1
    fi

    printf '%s' "$python_cmd"
}

check_env_file() {
    if [[ ! -f "$ENV_FILE" ]]; then
        warn "No .env file found"
        printf '\n'
        printf 'To use this tool, you need Trello API credentials.\n'
        printf '\n'
        printf '%sQuick Setup:%s\n' "$BOLD" "$NC"
        printf '  1. Get API key: %shttps://trello.com/app-key%s\n' "$CYAN" "$NC"
        printf '  2. Generate token from the same page\n'
        printf '  3. Create .env file:\n'
        printf '\n'
        printf '     %scp .env.example .env%s\n' "$CYAN" "$NC"
        printf '     %s# Edit .env with your credentials%s\n' "$CYAN" "$NC"
        printf '\n'
        printf 'Or run with --setup-help for detailed instructions.\n'
        printf '\n'
        return 1
    fi

    # Security: Check .env permissions
    if [[ "$(uname)" != "MINGW"* ]]; then
        local perms
        perms=$(stat -f "%OLp" "$ENV_FILE" 2>/dev/null || stat -c "%a" "$ENV_FILE" 2>/dev/null || echo "")
        if [[ -n "$perms" && "$perms" != "600" && "$perms" != "400" ]]; then
            warn ".env file permissions are too open (${perms})"
            printf '  Recommended: chmod 600 %s\n' "$ENV_FILE"
        fi
    fi

    return 0
}

# =============================================================================
# Virtual Environment Management
# =============================================================================
setup_venv() {
    local python_cmd="$1"

    if [[ ! -d "$VENV_DIR" ]]; then
        step "Creating virtual environment..."
        "$python_cmd" -m venv "$VENV_DIR"
        success "Virtual environment created"
    fi
}

activate_venv() {
    # shellcheck source=/dev/null
    source "${VENV_DIR}/bin/activate"
}

install_deps() {
    # Skip if already installed and requirements unchanged
    if [[ -f "$INSTALLED_MARKER" ]]; then
        if [[ "$REQUIREMENTS_FILE" -ot "$INSTALLED_MARKER" ]]; then
            return 0
        fi
    fi

    step "Installing dependencies..."
    pip install --quiet --upgrade pip
    pip install --quiet -e "${SCRIPT_DIR}"

    # Mark as installed
    touch "$INSTALLED_MARKER"
    success "Dependencies installed"
}

# =============================================================================
# Main Execution
# =============================================================================
main() {
    local args=("$@")

    # Show help if no arguments provided
    if [[ ${#args[@]} -eq 0 ]]; then
        local python_cmd
        python_cmd=$(check_python) || exit 1
        setup_venv "$python_cmd"
        activate_venv
        install_deps
        exec trello-career-planner --help
    fi

    # Fast path for --help (skip env check)
    for arg in "${args[@]:-}"; do
        if [[ "$arg" == "--help" || "$arg" == "-h" ]]; then
            local python_cmd
            python_cmd=$(check_python) || exit 1
            setup_venv "$python_cmd"
            activate_venv
            install_deps
            exec trello-career-planner --help
        fi
        if [[ "$arg" == "--setup-help" ]]; then
            local python_cmd
            python_cmd=$(check_python) || exit 1
            setup_venv "$python_cmd"
            activate_venv
            install_deps
            exec trello-career-planner --setup-help
        fi
        if [[ "$arg" == "--dry-run" ]]; then
            local python_cmd
            python_cmd=$(check_python) || exit 1
            setup_venv "$python_cmd"
            activate_venv
            install_deps
            exec trello-career-planner --dry-run
        fi
    done

    printf '\n'
    printf '%sTrello Career Planner%s\n' "$BOLD" "$NC"
    printf '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
    printf '\n'

    # Check prerequisites
    step "Checking prerequisites..."
    local python_cmd
    python_cmd=$(check_python) || exit 1
    success "Python $(${python_cmd} --version 2>&1 | cut -d' ' -f2) found"

    # Setup virtual environment
    setup_venv "$python_cmd"
    activate_venv
    success "Virtual environment activated"

    # Install dependencies
    install_deps

    # Check credentials (unless dry-run)
    step "Checking credentials..."
    if ! check_env_file; then
        exit 1
    fi
    success "Credentials file found"

    # Run the application
    printf '\n'
    step "Creating your Trello board..."
    printf '\n'

    trello-career-planner "${args[@]:-}"

    printf '\n'
    success "Done!"
}

# =============================================================================
# Entry Point
# =============================================================================
main "$@"
