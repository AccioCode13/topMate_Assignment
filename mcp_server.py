# mcp_server.py
import sys
import json
import traceback
from db import query
from nl_to_sql import map_query_to_sql

def handle_request(req: dict) -> dict:
    qid = req.get("id") or req.get("request_id") or "1"
    text = req.get("query") or req.get("text") or req.get("question")
    if not text:
        return {"id": qid, "error": "No query text provided"}

    sql, params, desc = map_query_to_sql(text)
    if not sql:
        return {"id": qid, "error": desc}

    try:
        rows = query(sql, params if isinstance(params, tuple) else params)
        return {"id": qid, "description": desc, "sql": sql, "params": params, "result": rows}
    except Exception as e:
        tb = traceback.format_exc()
        return {"id": qid, "error": str(e), "trace": tb}

def run_loop():
    # read line-by-line from stdin
    # Each line should be a JSON object
    print(json.dumps({"status":"mcp_server_started"}), flush=True)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            resp = {"id": None, "error": "Invalid JSON input"}
            print(json.dumps(resp), flush=True)
            continue

        resp = handle_request(req)
        print(json.dumps(resp), flush=True)

if __name__ == "__main__":
    run_loop()
