# Kalvium MCP

Kalvium MCP is a [Model Context Protocol](https://modelcontextprotocol.io/) server for Claude Desktop that lets authenticated Kalvium students access their own Livebooks through Playwright browser automation. It uses your local Chrome profile to retrieve the Livebooks and lessons available to your Kalvium account, then returns lesson content as Markdown for use in Claude.

## Features

- ✓ List the Livebooks available to your Kalvium account.
- ✓ List lessons within a selected Livebook.
- ✓ Fetch individual lesson content.
- ✓ Convert lesson HTML into readable Markdown.
- ✓ Integrate directly with Claude Desktop through MCP.
- ✓ Install dependencies, Playwright, Chromium, and the MCP registration with `setup.py`.
- ✓ Migrate an existing browser profile to `profiles/default` automatically.

## Demo

> A GIF or screenshot demonstrating Kalvium MCP in Claude Desktop will be added here.

## Requirements

- Windows 10 or Windows 11
- Python 3.11 or later
- [Claude Desktop](https://claude.ai/download)
- An active Kalvium account

## Installation

Clone the repository and create a virtual environment:

```powershell
git clone https://github.com/L-Sandeep/kalvium-mcp
cd kalvium-mcp
python -m venv .venv
```

Activate the environment on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies and run the installer:

```powershell
pip install -r requirements.txt
python setup.py
```

## First-Time Setup

`setup.py` checks your environment before changing anything and skips work that is already complete. It will:

- verify Python, pip, FastMCP, Playwright, Claude Desktop, the Claude configuration, and your browser profile;
- install missing Python dependencies, including Playwright;
- install Playwright Chromium when it is not already available;
- create a valid empty Claude Desktop configuration if one is missing;
- register Kalvium MCP with Claude Desktop without removing other MCP servers;
- use `profiles/default` as the browser profile and migrate a legacy `playwright-profile` directory when present.

After setup, open the browser profile when prompted by the server and sign in to `https://app.kalvium.community` if you are not already authenticated. Keep the profile closed while Claude is using Kalvium MCP, because Chrome cannot share the same profile concurrently.

## Usage

1. Restart Claude Desktop after running `python setup.py`.
2. Start a new chat in Claude Desktop.
3. Ask Claude to use your Kalvium Livebooks.

Example prompts:

- `List my livebooks`
- `List lessons in Full Stack Web Development`
- `Explain Request Response Lifecycle`
- `Summarize lesson 1.4`
- `Open lesson 2.3`

Claude will invoke the MCP tools when the request requires your Kalvium content. The server only accesses `app.kalvium.community` and uses the authentication already stored in your local browser profile.

## Project Structure

```text
kalvium-mcp/
├── auth.py                 # Persistent Playwright profile and browser lifecycle
├── browser.py              # Browser debugging utility
├── markdown.py             # HTML-to-Markdown conversion helpers
├── scraper.py              # Kalvium Livebook and lesson scraping logic
├── server.py               # FastMCP server entry point
├── setup.py                # Idempotent Windows installer for Claude Desktop
├── tools.py                # MCP tool definitions
├── requirements.txt        # Runtime dependencies
├── pyproject.toml          # Package metadata and build configuration
├── dev/                    # Development and inspection scripts
├── docs/                   # Project documentation
├── installer/              # Installer-related assets
├── profiles/               # Local browser profiles (not committed)
├── samples/                # Saved sample output for development
└── src/kalvium_mcp/        # Python package namespace
```

## How It Works

```text
Claude Desktop
      ↓
FastMCP Server
      ↓
Playwright
      ↓
Authenticated Kalvium Browser Profile
      ↓
Lesson Extraction
      ↓
Markdown Response
```

Claude Desktop calls the FastMCP server over the MCP protocol. The server opens a persistent Chrome context with Playwright, using the local authenticated profile in `profiles/default`. It reads accessible Livebook pages, extracts the requested lesson information, converts lesson HTML to Markdown, and sends the result back to Claude.

## Troubleshooting

### Claude Desktop is not installed

Install Claude Desktop from the [official download page](https://claude.ai/download), open it once, and run `python setup.py` again.

### Browser profile is missing

The server creates `profiles/default` automatically. Sign in to Kalvium in the Chrome window opened by the server, then close the browser window before using Claude Desktop again.

### Login has expired

Run the server or a browser utility, sign in again at `https://app.kalvium.community`, and close Chrome cleanly so the updated session is saved in `profiles/default`.

### Playwright is not installed

Activate the virtual environment and run:

```powershell
python setup.py
```

The installer checks for Playwright and installs missing dependencies.

### Kalvium MCP does not appear in Claude

Restart Claude Desktop after installation. If it is still unavailable, run `python setup.py` again and confirm that its Claude Desktop configuration check succeeds. Ensure the configured Python executable is the same virtual environment where dependencies were installed.

## Roadmap

- [x] GitHub repository
- [x] MCP server
- [x] Playwright automation
- [x] Lesson extraction
- [x] Automatic installer
- [ ] Automatic login flow
- [ ] Self-test after installation
- [ ] Search lessons
- [ ] Search lesson content
- [ ] Package for pip installation
- [ ] macOS support
- [ ] Linux support

## Contributing

Contributions are welcome. Please open an issue to discuss significant changes, then submit a focused pull request with a clear description and appropriate tests or manual verification notes.

## License

MIT License. A license file will be added to the repository.
