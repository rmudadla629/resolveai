"""Transactional cancellation review for fictional orders only."""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "runtime" / "reviews.sqlite3"


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.executescript('''
    CREATE TABLE IF NOT EXISTS requests (
      id INTEGER PRIMARY KEY, order_id TEXT NOT NULL, state TEXT NOT NULL,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP, decided_at TEXT);
    CREATE UNIQUE INDEX IF NOT EXISTS one_pending ON requests(order_id) WHERE state='pending';
    CREATE TABLE IF NOT EXISTS overrides (order_id TEXT PRIMARY KEY, status TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS audit (
      id INTEGER PRIMARY KEY, request_id INTEGER NOT NULL, event TEXT NOT NULL,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    ''')
    if "actor" not in {r["name"] for r in db.execute("PRAGMA table_info(audit)")}:
        db.execute("ALTER TABLE audit ADD COLUMN actor TEXT NOT NULL DEFAULT 'legacy'")
        db.commit()
    return db


def effective_order(order_id, db):
    source = Path(__file__).resolve().parent.parent / "data" / "orders.json"
    order = next((o for o in json.loads(source.read_text()) if o["order_id"] == order_id), None)
    if order:
        override = db.execute("SELECT status FROM overrides WHERE order_id=?", (order_id,)).fetchone()
        if override:
            order["status"] = override["status"]
    return order


def submit(order_id, actor="reviewer"):
    order_id = order_id.strip().upper()
    db = connect()
    try:
        with db:
            db.execute("BEGIN IMMEDIATE")
            order = effective_order(order_id, db)
            if not order:
                return "No matching demo order was found."
            if order["status"] != "processing":
                return "Only processing orders can be submitted for cancellation review."
            pending = db.execute("SELECT id FROM requests WHERE order_id=? AND state='pending'", (order_id,)).fetchone()
            if pending:
                return f'Request #{pending["id"]} is already pending review.'
            request_id = db.execute("INSERT INTO requests(order_id,state) VALUES (?, 'pending')", (order_id,)).lastrowid
            db.execute("INSERT INTO audit(request_id,event,actor) VALUES (?, 'submitted', ?)", (request_id, actor))
            return f"Request #{request_id} submitted for review. The order has not been cancelled."
    finally:
        db.close()


def decide(request_id, action):
    if action not in ("approve", "reject"):
        return "Invalid decision."
    db = connect()
    try:
        with db:
            db.execute("BEGIN IMMEDIATE")
            request = db.execute("SELECT * FROM requests WHERE id=?", (request_id,)).fetchone()
            if not request or request["state"] != "pending":
                return "This request is missing or has already been reviewed."
            state = "rejected"
            if action == "approve":
                order = effective_order(request["order_id"], db)
                if not order or order["status"] != "processing":
                    state = "blocked"
                else:
                    state = "approved"
                    db.execute("INSERT OR REPLACE INTO overrides VALUES (?, 'cancelled')", (request["order_id"],))
            db.execute("UPDATE requests SET state=?, decided_at=CURRENT_TIMESTAMP WHERE id=?", (state, request_id))
            db.execute("INSERT INTO audit(request_id,event,actor) VALUES (?, ?, 'reviewer')", (request_id, state))
            return f"Request #{request_id}: {state}."
    finally:
        db.close()


def snapshot():
    db = connect()
    try:
        return ([dict(r) for r in db.execute("SELECT * FROM requests ORDER BY id DESC")],
                [dict(r) for r in db.execute("SELECT * FROM audit ORDER BY id DESC")])
    finally:
        db.close()
