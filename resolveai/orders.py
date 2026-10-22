"""Read-only order tool and grounded demo responses; no model calls."""

import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "orders.json"


def lookup_order(order_id: str) -> dict | None:
    normalized = order_id.strip().upper()
    orders = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    order = next((order for order in orders if order["order_id"] == normalized), None)
    from . import reviews
    if order and reviews.DB_PATH.exists():
        db = reviews.connect()
        try:
            override = db.execute("SELECT status FROM overrides WHERE order_id=?", (normalized,)).fetchone()
            if override:
                order["status"] = override["status"]
        finally:
            db.close()
    return order


def answer_order(order_id: str) -> tuple[int, dict]:
    if not order_id.strip():
        return 400, {"mode": "deterministic_demo", "message": "Please supply a demo order ID."}
    order = lookup_order(order_id)
    if order is None:
        return 404, {"mode": "deterministic_demo", "message": "No matching demo order was found. Check the order ID."}
    message = f"Your order {order['order_id']} ({order['item']}) is {order['status']}."
    if order["tracking_id"]:
        message += f" Demo tracking reference: {order['tracking_id']}."
    return 200, {"mode": "deterministic_demo", "message": message, "order": order,
                 "source": f"demo-orders:{order['order_id']}"}
