"""Bounded local request metadata, without prompts or response text."""

import logging
import sqlite3
from html import escape
from pathlib import Path
from time import perf_counter
from uuid import uuid4

TRACE_PATH = Path(__file__).resolve().parent.parent / "runtime" / "traces.sqlite3"


def connect():
    TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(TRACE_PATH, timeout=5)
    db.row_factory = sqlite3.Row
    db.execute('''CREATE TABLE IF NOT EXISTS traces (
        id TEXT PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        status INTEGER, outcome TEXT, tool TEXT, retrieval_method TEXT, elapsed_ms REAL)''')
    return db


def record(trace_id, status, body, elapsed_ms):
    db = connect()
    try:
        with db:
            db.execute("INSERT INTO traces(id,status,outcome,tool,retrieval_method,elapsed_ms) VALUES (?,?,?,?,?,?)",
                       (trace_id, status, body.get("outcome", "unknown"), body.get("tool", "none"),
                        body.get("retrieval_method", "n/a"), elapsed_ms))
            db.execute("DELETE FROM traces WHERE rowid NOT IN (SELECT rowid FROM traces ORDER BY rowid DESC LIMIT 1000)")
    finally:
        db.close()


def traced_answer(question, handler):
    trace_id = uuid4().hex
    start = perf_counter()
    try:
        status, body = handler(question)
    except Exception:
        # Do not persist exception text, which could contain customer input.
        status, body = 500, {"mode": "local_ai", "outcome": "internal_error",
                             "message": "Something went wrong while processing this request. Please try again."}
    elapsed = round((perf_counter() - start) * 1000, 2)
    try:
        record(trace_id, status, body, elapsed)
    except (OSError, sqlite3.Error):
        logging.warning("Trace storage unavailable for request %s", trace_id)
        return status, {**body, "trace_id": trace_id, "trace_saved": False}
    return status, {**body, "trace_id": trace_id, "trace_saved": True}


def render_traces():
    try:
        db = connect()
        try:
            rows = [dict(row) for row in db.execute("SELECT * FROM traces ORDER BY rowid DESC LIMIT 100")]
            total, errors, average = db.execute("SELECT COUNT(*), COALESCE(SUM(status>=500),0), COALESCE(AVG(elapsed_ms),0) FROM traces").fetchone()
        finally:
            db.close()
    except (OSError, sqlite3.Error):
        return b'<!doctype html><title>Trace storage unavailable</title><h1>Trace storage unavailable</h1><a href="/">Back to support</a>'
    table = "".join('<tr>' + ''.join(f'<td>{escape(str(row[key]))}</td>' for key in
                    ("created_at", "id", "outcome", "status", "tool", "retrieval_method", "elapsed_ms")) + '</tr>' for row in rows)
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ResolveAI request traces</title>
<style>body{{margin:32px;font:16px/1.6 system-ui;color:#17243b}}td,th{{padding:10px;border-bottom:1px solid #ddd;text-align:left}}.scroll{{overflow:auto}}</style>
<a href="/">Back to support</a><h1>Request traces</h1><p>Local demo metadata for AI question submissions. Prompts, order IDs, and response text are not stored here. No sign-in: keep this page local.</p>
<p>Retained requests: {total} · Server/model errors (HTTP 5xx): {errors} · Mean processing time: {average:.1f} ms</p>
<p>Newest 100 of up to 1,000 retained requests. Times are UTC. Duration includes model routing and retrieval; excludes form parsing, page rendering, and network delivery. HTTP status and outcomes do not measure answer accuracy. Refresh to see new requests.</p>
<div class="scroll"><table><thead><tr><th>Time (UTC)</th><th>Trace ID</th><th>Outcome</th><th>HTTP</th><th>Tool</th><th>Search</th><th>Time (ms)</th></tr></thead><tbody>{table or '<tr><td colspan="7">No requests recorded yet. Ask a question on the support page.</td></tr>'}</tbody></table></div></html>'''.encode()
