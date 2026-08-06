# Kalvium Livebooks MCP

A read-only MCP server that lets an MCP client such as Claude Desktop browse the
Livebooks accessible through your own existing Kalvium browser session. It uses
Playwright's persistent profile and does not implement, bypass, or reverse
engineer authentication.

## Setup

Requires Python 3.13 and Google Chrome.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chrome
```

Log into `https://app.kalvium.community` in the Chrome profile stored in
`playwright-profile`. The profile must not be open in another Chrome process
when the MCP server is running.

## Claude Desktop configuration

Add this server to Claude Desktop's MCP configuration, updating the paths for
your installation:

```json
{
  "mcpServers": {
    "kalvium-livebooks": {
      "command": "C:\\Users\\sande\\kalvium-mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\sande\\kalvium-mcp\\server.py"]
    }
  }
}
```

Restart Claude Desktop after saving the configuration.

## Tools

- `list_livebooks`: lists Livebooks you can access.
- `list_lessons(livebook_id)`: expands each module and lists its lessons.
- `get_lesson(url)`: returns a lesson converted to Markdown for studying.

The scraper opens pages only on `app.kalvium.community`, validates lesson URLs,
and closes Chrome after each request.
