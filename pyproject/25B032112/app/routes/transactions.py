"""/transactions and /transfer endpoints."""
import time
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request
from psycopg import errors as pg_errors

from app.db import get_conn
from app.errors import ApiError

bp = Blueprint("transactions", __name__)


def _amount(value):
    """Parse a positive money amount; raise 400 otherwise."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ApiError(400, "amount must be a number")
    if amount <= 0:
        raise ApiError(400, "amount must be greater than 0")
    return amount


def _int_field(data, name):
    value = data.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ApiError(400, f"{name} (integer) is required")
    return value


@bp.post("/transactions")
def create_transaction():
    """Record a single DEBIT or CREDIT on one account."""
    data = request.get_json(silent=True) or {}
    account_id = _int_field(data, "account_id")
    amount = _amount(data.get("amount"))
    tx_type = str(data.get("tx_type", "")).upper()
    if tx_type not in ("DEBIT", "CREDIT"):
        raise ApiError(400, "tx_type must be DEBIT or CREDIT")
    signed = -amount if tx_type == "DEBIT" else amount

    with get_conn() as conn:
        try:
            # lock the row so two requests can't change the same balance at once
            if conn.execute("SELECT 1 FROM accounts WHERE account_id = %s FOR UPDATE",
                            (account_id,)).fetchone() is None:
                raise ApiError(404, f"Account {account_id} not found")
            # CHECK (balance >= 0) rejects an overdraft -> CheckViolation -> 400
            new_balance = conn.execute(
                "UPDATE accounts SET balance = balance + %s WHERE account_id = %s RETURNING balance",
                (signed, account_id),
            ).fetchone()[0]
            tx_id = conn.execute(
                "INSERT INTO transactions (account_id, amount, tx_type) VALUES (%s, %s, %s) "
                "RETURNING tx_id",
                (account_id, amount, tx_type),
            ).fetchone()[0]
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return jsonify({"tx_id": tx_id, "account_id": account_id, "balance": str(new_balance)}), 201

def do_transfer(from_acc, to_acc, amount):
    with get_conn() as conn:
        try:
            # Task 4.3: SERIALIZABLE for this transaction only (must be the first statement)
            conn.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")

            # Task 4.5: lock both rows in ascending id order -> no deadlocks
            for acc in sorted([from_acc, to_acc]):
                if conn.execute("SELECT 1 FROM accounts WHERE account_id = %s FOR UPDATE",
                                (acc,)).fetchone() is None:
                    raise ApiError(404, f"Account {acc} not found")

            # Task 4.2: SAVEPOINT so a failed transfer step can be undone on its own
            conn.execute("SAVEPOINT before_transfer")
            try:
                conn.execute("UPDATE accounts SET balance = balance - %s WHERE account_id = %s",
                             (amount, from_acc))
                conn.execute("UPDATE accounts SET balance = balance + %s WHERE account_id = %s",
                             (amount, to_acc))
                conn.execute(
                    "INSERT INTO transactions (account_id, amount, tx_type) "
                    "VALUES (%s, %s, 'DEBIT'), (%s, %s, 'CREDIT')",
                    (from_acc, amount, to_acc, amount),
                )
                result = ({"status": "completed", "from": from_acc, "to": to_acc,
                           "amount": str(amount)}, 200)
            except pg_errors.CheckViolation:
                # insufficient funds: undo only the transfer step, keep the transaction alive
                conn.execute("ROLLBACK TO SAVEPOINT before_transfer")
                conn.execute(
                    "INSERT INTO transactions (account_id, amount, tx_type, status) "
                    "VALUES (%s, %s, 'DEBIT', 'FAILED')",
                    (from_acc, amount),
                )
                result = ({"status": "failed", "reason": "insufficient funds"}, 400)

            conn.commit()          # Task 4.1: both UPDATEs (or the FAILED log row) commit together
            return result
        except Exception:
            conn.rollback()        # any other error: nothing from this transaction persists
            raise


@bp.post("/transfer")
def transfer():
    data = request.get_json(silent=True) or {}
    from_acc = _int_field(data, "from_account")
    to_acc = _int_field(data, "to_account")
    if from_acc == to_acc:
        raise ApiError(400, "from_account and to_account must differ")
    amount = _amount(data.get("amount"))

    body, status = do_transfer(from_acc, to_acc, amount)
    return jsonify(body), status