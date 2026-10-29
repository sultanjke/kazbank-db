"""/accounts endpoints."""
from flask import Blueprint, jsonify, request

from app.db import get_conn
from app.errors import ApiError

bp = Blueprint("accounts", __name__)


@bp.get("/accounts")
def list_accounts():
    customer_id = request.args.get("customer_id", type=int)   # None if missing or not an int
    if customer_id is None:
        raise ApiError(400, "Query parameter customer_id (integer) is required")
    with get_conn() as conn:
        if conn.execute("SELECT 1 FROM customers WHERE customer_id = %s",
                        (customer_id,)).fetchone() is None:
            raise ApiError(404, f"Customer {customer_id} not found")
        rows = conn.execute(
            "SELECT account_id, account_number, balance FROM accounts "
            "WHERE customer_id = %s ORDER BY account_id",
            (customer_id,),
        ).fetchall()
    return jsonify([
        {"account_id": r[0], "account_number": r[1], "balance": str(r[2])} for r in rows
    ])