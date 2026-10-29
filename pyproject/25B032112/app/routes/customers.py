"""/customers endpoints."""
from flask import Blueprint, jsonify, request

from app.db import get_conn
from app.errors import ApiError

bp = Blueprint("customers", __name__)


def _row(r):
    return {"id": r[0], "name": r[1], "email": r[2], "city": r[3]}


@bp.get("/customers")
def list_customers():
    city = request.args.get("city")          # None when not given
    if city:
        sql = ("SELECT customer_id, full_name, email, city FROM customers "
               "WHERE city = %s ORDER BY customer_id")
        args = (city,)
    else:
        sql = "SELECT customer_id, full_name, email, city FROM customers ORDER BY customer_id"
        args = ()
    with get_conn() as conn:
        rows = conn.execute(sql, args).fetchall()
    return jsonify([_row(r) for r in rows])


@bp.post("/customers")
def create_customer():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError(400, "Request body must be a JSON object")
    # full_name is deliberately NOT checked here: a missing name reaches the
    # database and comes back as NotNullViolation -> 400 (Step 5 test).
    with get_conn() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO customers (full_name, email, city) "
                "VALUES (%s, %s, %s) RETURNING customer_id",
                (data.get("full_name"), data.get("email"), data.get("city") or "Almaty"),
            )
            new_id = cur.fetchone()[0]
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return jsonify({"customer_id": new_id}), 201


@bp.put("/customers/<int:cid>")
def update_customer(cid):
    data = request.get_json(silent=True) or {}
    if not data.get("full_name") or not data.get("city"):
        raise ApiError(400, "full_name and city are required")
    with get_conn() as conn:
        try:
            cur = conn.execute(
                "UPDATE customers SET full_name = %s, city = %s, email = COALESCE(%s, email) "
                "WHERE customer_id = %s",
                (data["full_name"], data["city"], data.get("email"), cid),
            )
            if cur.rowcount == 0:
                raise ApiError(404, f"Customer {cid} not found")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return jsonify({"updated": cid})


@bp.delete("/customers/<int:cid>")
def delete_customer(cid):
    with get_conn() as conn:
        try:
            cur = conn.execute("DELETE FROM customers WHERE customer_id = %s", (cid,))
            if cur.rowcount == 0:
                raise ApiError(404, f"Customer {cid} not found")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return jsonify({"deleted": cid})