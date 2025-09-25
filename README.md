# MCP server for IPL (Claude Desktop)

## Prereqs
- MySQL running with `ipl` DB and your ingestion completed.
- Python 3.8+ installed.
- Install dependencies:
    python3 -m pip install -r requirements.txt

## Env
Set MySQL credentials if not default:
export MYSQL_USER=root
export MYSQL_PASS='Shreya1322#'
export MYSQL_DB=ipl
export MYSQL_HOST=localhost
export MYSQL_PORT=3306

## Run locally (manual testing)
Option A — Test HTTP:
    uvicorn fastapi_app:app --reload --port 8000
    
The server expects newline-delimited JSON objects on stdin, for example:
{"id":"1","query":"Who scored the most runs?"}

It will write a JSON response to stdout. Example:
{"id":"1","description":"Top run scorers","sql":"SELECT ...","result":[{"player":"X","runs":123}, ...]}

## Claude Desktop config (example)
In Claude Desktop configuration add a server entry that spawns this script:

"servers": {
  "ipl_mcp": {
    "command": "python3",
    "args": ["./mcp_server.py"],
    "cwd": "/full/path/to/assignment"
  }
}
