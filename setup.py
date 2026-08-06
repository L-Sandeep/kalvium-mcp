"""Install and register Kalvium MCP for Claude Desktop.

Run this script from the virtual environment that Claude Desktop should use:
    python setup.py
"""

from __future__ import annotations

import importlib.metadata
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SERVER_NAME = "kalvium"
MINIMUM_PYTHON = (3, 11)
PROJECT_DIRECTORY = Path(__file__).resolve().parent
REQUIREMENTS_FILE = PROJECT_DIRECTORY / "requirements.txt"
SERVER_FILE = PROJECT_DIRECTORY / "server.py"
DEFAULT_PROFILE_DIRECTORY = PROJECT_DIRECTORY / "profiles" / "default"
LEGACY_PROFILE_DIRECTORY = PROJECT_DIRECTORY / "playwright-profile"
REQUIRED_PACKAGES = {
    "beautifulsoup4": "beautifulsoup4",
    "fastmcp": "fastmcp",
    "markdownify": "markdownify",
    "playwright": "playwright",
    "pydantic": "pydantic",
}


class SetupError(RuntimeError):
    """An expected setup prerequisite is missing or invalid."""


@dataclass(frozen=True)
class PreflightResults:
    """Information collected before the installer changes the system."""

    missing_packages: tuple[str, ...]
    chromium_installed: bool
    claude_config_file: Path
    mcp_already_installed: bool
    existing_profile_detected: bool


def success(message: str) -> None:
    """Print a successful setup status."""
    print_status("\u2713", "[OK]", message)


def info(message: str) -> None:
    """Print a non-error setup status."""
    print_status("\u2022", "[INFO]", message)


def print_status(symbol: str, fallback: str, message: str) -> None:
    """Print a Unicode status marker, falling back for legacy Windows consoles."""
    try:
        print(f"{symbol} {message}")
    except UnicodeEncodeError:
        print(f"{fallback} {message}")


def check_python_version() -> None:
    """Require the Python version declared by the project."""
    version = sys.version_info
    if version[:2] < MINIMUM_PYTHON:
        required = ".".join(map(str, MINIMUM_PYTHON))
        detected = f"{version.major}.{version.minor}.{version.micro}"
        raise SetupError(f"Python {required}+ is required; found Python {detected}.")
    success(f"Python {version.major}.{version.minor}.{version.micro} detected")


def pip_is_available() -> bool:
    """Return whether pip can be invoked by the active Python interpreter."""
    return subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0


def ensure_pip() -> None:
    """Install pip only when the active Python environment does not have it."""
    if pip_is_available():
        success("pip available")
        return

    info("pip is missing; installing pip...")
    run_command([sys.executable, "-m", "ensurepip", "--upgrade"])
    if not pip_is_available():
        raise SetupError("pip could not be installed. Reinstall Python with pip enabled.")
    success("pip installed")


def missing_project_packages() -> tuple[str, ...]:
    """Return required distribution names that are absent from this environment."""
    missing: list[str] = []
    for distribution_name in REQUIRED_PACKAGES:
        try:
            importlib.metadata.version(distribution_name)
        except importlib.metadata.PackageNotFoundError:
            missing.append(distribution_name)
    return tuple(missing)


def check_project_packages() -> tuple[str, ...]:
    """Report the FastMCP and Playwright dependency status before installation."""
    missing_packages = missing_project_packages()
    missing_set = set(missing_packages)

    for package_name, label in (("fastmcp", "FastMCP"), ("playwright", "Playwright")):
        if package_name in missing_set:
            info(f"{label} is not installed")
        else:
            success(f"{label} installed")

    other_missing = sorted(missing_set - {"fastmcp", "playwright"})
    if other_missing:
        info(f"Additional project dependencies missing: {', '.join(other_missing)}")
    return missing_packages


def install_project_packages(missing_packages: tuple[str, ...]) -> None:
    """Install requirements only when at least one required package is absent."""
    if not missing_packages:
        success("Python dependencies already installed")
        return
    if not REQUIREMENTS_FILE.is_file():
        raise SetupError(f"Requirements file not found: {REQUIREMENTS_FILE}")

    info("Installing missing Python dependencies...")
    run_command([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])
    still_missing = missing_project_packages()
    if still_missing:
        raise SetupError(f"Dependencies are still missing: {', '.join(still_missing)}")
    success("Python dependencies installed")


def chromium_is_installed() -> bool:
    """Return whether Playwright reports an installed Chromium browser."""
    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "--list"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and "chromium" in result.stdout.lower()


def check_chromium() -> bool:
    """Report whether Playwright's Chromium browser is already installed."""
    installed = chromium_is_installed()
    if installed:
        success("Chromium installed")
    else:
        info("Chromium is not installed")
    return installed


def install_chromium(already_installed: bool) -> None:
    """Install Playwright Chromium only when it is not already available."""
    if already_installed:
        success("Skipping Chromium installation")
        return

    info("Installing Chromium...")
    run_command([sys.executable, "-m", "playwright", "install", "chromium"])
    if not chromium_is_installed():
        raise SetupError("Chromium installation did not complete successfully.")
    success("Chromium installed")


def claude_config_file() -> Path:
    """Return Claude Desktop's platform-specific MCP configuration path."""
    if sys.platform == "win32":
        app_data = os.environ.get("APPDATA")
        if not app_data:
            raise SetupError("APPDATA is unavailable; cannot locate Claude Desktop settings.")
        return Path(app_data) / "Claude" / "claude_desktop_config.json"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def claude_desktop_is_installed(config_file: Path) -> bool:
    """Return whether Claude Desktop installation data or executable is present."""
    if config_file.parent.is_dir():
        return True

    if sys.platform == "win32":
        executable_locations = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "claude" / "Claude.exe",
            Path(os.environ.get("PROGRAMFILES", "")) / "Claude" / "Claude.exe",
        ]
        return any(location.is_file() for location in executable_locations)

    if sys.platform == "darwin":
        return Path("/Applications/Claude.app").is_dir()
    return False


def check_claude_desktop(config_file: Path) -> None:
    """Stop before making installation changes when Claude Desktop is unavailable."""
    if not claude_desktop_is_installed(config_file):
        raise SetupError(
            "Claude Desktop was not found. Install and open Claude Desktop once, then run "
            "this installer again."
        )
    success("Claude Desktop detected")


def load_claude_config(config_file: Path) -> dict[str, Any]:
    """Load Claude's config, creating a valid empty config when it is missing."""
    if not config_file.exists():
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config = {"mcpServers": {}}
        write_claude_config(config_file, config)
        success(f"Created Claude Desktop config: {config_file}")
        return config

    try:
        config = json.loads(config_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SetupError(
            f"Claude Desktop config contains invalid JSON: {config_file}. Fix it before rerunning setup."
        ) from exc

    if not isinstance(config, dict):
        raise SetupError(f"Claude Desktop config must contain a JSON object: {config_file}")
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    if not isinstance(config["mcpServers"], dict):
        raise SetupError("Claude Desktop config field 'mcpServers' must be a JSON object.")

    success(f"Claude Desktop config found: {config_file}")
    return config


def write_claude_config(config_file: Path, config: dict[str, Any]) -> None:
    """Write a readable Claude Desktop config without discarding other servers."""
    config_file.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def check_mcp_installation(config: dict[str, Any]) -> bool:
    """Return whether the Kalvium server is already registered with Claude Desktop."""
    installed = SERVER_NAME in config["mcpServers"]
    if installed:
        success(f"Existing MCP installation found: {SERVER_NAME}")
    else:
        info(f"MCP installation not found: {SERVER_NAME}")
    return installed


def install_mcp(config_file: Path, config: dict[str, Any], already_installed: bool) -> None:
    """Register this server while preserving all pre-existing MCP entries."""
    if already_installed:
        success("Skipping MCP registration")
        return

    config["mcpServers"][SERVER_NAME] = {
        "command": str(Path(sys.executable).resolve()),
        "args": [str(SERVER_FILE)],
    }
    write_claude_config(config_file, config)
    success("Kalvium MCP registered with Claude Desktop")


def check_browser_profile() -> bool:
    """Return whether the default Kalvium profile exists and contains data."""
    profile_exists = (
        DEFAULT_PROFILE_DIRECTORY.is_dir()
        and any(DEFAULT_PROFILE_DIRECTORY.iterdir())
    )
    if profile_exists:
        success("Existing Kalvium profile detected")
    else:
        print("No Kalvium profile found.")
    return profile_exists


def run_first_time_login() -> None:
    """Run interactive login and report failures as installer errors."""
    print()
    print("Starting first-time login...")

    try:
        from auth import first_time_login

        first_time_login()
    except Exception as exc:
        raise SetupError(
            "First-time Kalvium login failed. Complete the login in Chrome and run setup again."
        ) from exc


def run_command(command: list[str]) -> None:
    """Run an installer command and show it for troubleshooting."""
    print(f"\n>>> {' '.join(command)}")
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise SetupError(f"Command failed with exit code {exc.returncode}: {' '.join(command)}") from exc


def preflight() -> PreflightResults:
    """Perform every prerequisite check before installing dependencies or browsers."""
    check_python_version()
    if pip_is_available():
        success("pip available")
    else:
        info("pip is not installed")

    missing_packages = check_project_packages()
    chromium_installed = check_chromium() if "playwright" not in missing_packages else False
    if "playwright" in missing_packages:
        info("Chromium check deferred until Playwright is installed")

    config_file = claude_config_file()
    check_claude_desktop(config_file)
    config = load_claude_config(config_file)
    mcp_already_installed = check_mcp_installation(config)
    existing_profile_detected = check_browser_profile()

    return PreflightResults(
        missing_packages=missing_packages,
        chromium_installed=chromium_installed,
        claude_config_file=config_file,
        mcp_already_installed=mcp_already_installed,
        existing_profile_detected=existing_profile_detected,
    )


def main() -> None:
    """Run preflight checks, then install only missing components."""
    print("=" * 50)
    print("Kalvium MCP Setup")
    print("=" * 50)

    results = preflight()
    ensure_pip()
    install_project_packages(results.missing_packages)

    chromium_installed = results.chromium_installed
    if "playwright" in results.missing_packages:
        chromium_installed = check_chromium()
    install_chromium(chromium_installed)

    if not results.existing_profile_detected:
        run_first_time_login()

    config = load_claude_config(results.claude_config_file)
    install_mcp(results.claude_config_file, config, results.mcp_already_installed)

    print("\nSetup complete. Restart Claude Desktop to load the Kalvium MCP server.")


if __name__ == "__main__":
    try:
        main()
    except SetupError as exc:
        print(f"\nSetup failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
