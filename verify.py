"""Verify that Kalvium MCP is ready to use with Claude Desktop."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import installer


@dataclass(frozen=True)
class VerificationFailure:
    """A failed readiness check and the action needed to resolve it."""

    explanation: str
    action: str


def check_python_version() -> VerificationFailure | None:
    """Validate the active Python version using the installer check."""
    try:
        installer.check_python_version()
    except installer.SetupError as exc:
        return VerificationFailure(str(exc), "Install a supported Python version, then recreate .venv.")
    return None


def check_pip() -> VerificationFailure | None:
    """Verify that pip is available without attempting installation."""
    if installer.pip_is_available():
        installer.success("pip available")
        return None
    return VerificationFailure("pip is not available.", "Run:\n\npython installer.py")


def check_dependencies() -> list[VerificationFailure]:
    """Verify FastMCP, Playwright, and the remaining project dependencies."""
    missing_packages = set(installer.check_project_packages())
    failures: list[VerificationFailure] = []

    if "fastmcp" in missing_packages:
        failures.append(VerificationFailure("FastMCP is not installed.", "Run:\n\npython installer.py"))
    if "playwright" in missing_packages:
        failures.append(VerificationFailure("Playwright is not installed.", "Run:\n\npython installer.py"))

    other_missing = sorted(missing_packages - {"fastmcp", "playwright"})
    if other_missing:
        failures.append(
            VerificationFailure(
                f"Required Python dependencies are missing: {', '.join(other_missing)}.",
                "Run:\n\npython installer.py",
            )
        )
    return failures


def check_chromium() -> VerificationFailure | None:
    """Verify Playwright Chromium using the installer check."""
    if installer.check_chromium():
        return None
    return VerificationFailure("Chromium is not installed.", "Run:\n\npython installer.py")


def check_claude_desktop() -> tuple[Path | None, VerificationFailure | None]:
    """Verify that Claude Desktop is installed and return its config path."""
    try:
        config_file = installer.claude_config_file()
    except installer.SetupError as exc:
        return None, VerificationFailure(str(exc), "Install Claude Desktop, then run:\n\npython installer.py")

    if installer.claude_desktop_is_installed(config_file):
        installer.success("Claude Desktop detected")
        return config_file, None
    return None, VerificationFailure(
        "Claude Desktop is not installed.",
        "Install and open Claude Desktop once, then run:\n\npython installer.py",
    )


def check_claude_config(config_file: Path | None) -> tuple[dict | None, VerificationFailure | None]:
    """Validate an existing Claude Desktop config without creating one."""
    if config_file is None:
        return None, None
    if not config_file.is_file():
        return None, VerificationFailure(
            "Claude Desktop config file is missing.",
            "Run:\n\npython installer.py",
        )

    try:
        return installer.load_claude_config(config_file), None
    except installer.SetupError as exc:
        return None, VerificationFailure(str(exc), "Fix the configuration, then run:\n\npython installer.py")


def check_mcp_registration(config: dict | None) -> VerificationFailure | None:
    """Verify the Kalvium MCP registration using the installer check."""
    if config is None:
        return None
    if installer.check_mcp_installation(config):
        return None
    return VerificationFailure(
        "Kalvium MCP is not registered with Claude Desktop.",
        "Run:\n\npython installer.py",
    )


def check_browser_profile() -> VerificationFailure | None:
    """Verify the non-empty default browser profile using the installer check."""
    if installer.check_browser_profile():
        return None
    return VerificationFailure(
        "Kalvium browser profile is missing or empty.",
        "Run:\n\npython installer.py",
    )


def print_failures(failures: list[VerificationFailure]) -> None:
    """Print all failed checks and their corresponding recovery actions."""
    print("\nKalvium MCP needs attention:\n")
    for failure in failures:
        print(f"- {failure.explanation}")
        print(f"  {failure.action}\n")


def main() -> int:
    """Run every readiness check without modifying the user's installation."""
    print("=" * 40)
    print("Kalvium MCP Verification")
    print("=" * 40)

    failures: list[VerificationFailure] = []

    for check in (check_python_version, check_pip, check_chromium, check_browser_profile):
        failure = check()
        if failure is not None:
            failures.append(failure)

    failures.extend(check_dependencies())

    config_file, failure = check_claude_desktop()
    if failure is not None:
        failures.append(failure)

    config, failure = check_claude_config(config_file)
    if failure is not None:
        failures.append(failure)

    failure = check_mcp_registration(config)
    if failure is not None:
        failures.append(failure)

    if failures:
        print_failures(failures)
        return 1

    print()
    installer.success("Everything looks good.")
    print("\nYou can now open Claude Desktop.")
    print("\nSuggested first prompt:\n")
    print("List my livebooks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



