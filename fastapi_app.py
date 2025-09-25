# fastapi_app.py
from fastapi import FastAPI
from pydantic import BaseModel
from db import query
from nl_to_sql import map_query_to_sql

app = FastAPI()

class Q(BaseModel):
    query: str

@app.post("/query")
def post_query(q: Q):
    sql, params, desc = map_query_to_sql(q.query)
    if not sql:
        return {"error": desc}
    rows = query(sql, params if isinstance(params, tuple) else params)
    return {"description": desc, "sql": sql, "params": params, "result": rows}
