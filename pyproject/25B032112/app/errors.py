"""Step 5: map psycopg3 exceptions to JSON responses with the right HTTP status."""
import psycopg
from flask import jsonify
from psycopg import errors as pg_errors
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    """Raise for validation problems and missing resources."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def register_error_handlers(app):
    # Flask picks the most specific matching class, so order here doesn't matter.

    @app.errorhandler(ApiError)
    def api_error(e):
        return jsonify({"error": e.message}), e.status

    @app.errorhandler(pg_errors.UniqueViolation)
    def unique_violation(e):
        return jsonify({"error": "Duplicate value", "detail": e.diag.message_detail}), 409

    @app.errorhandler(pg_errors.NotNullViolation)
    def not_null_violation(e):
        return jsonify({"error": f"Missing required field: {e.diag.column_name}"}), 400

    @app.errorhandler(pg_errors.CheckViolation)
    def check_violation(e):
        return jsonify({"error": "Constraint check failed", "constraint": e.diag.constraint_name}), 400

    @app.errorhandler(pg_errors.ForeignKeyViolation)
    def fk_violation(e):
        return jsonify({"error": "Referenced by other rows", "detail": e.diag.message_detail}), 409

    # SerializationFailure / DeadlockDetected are subclasses of OperationalError,
    # so they need their own handler or they'd be reported as "database down".
    @app.errorhandler(pg_errors.SerializationFailure)
    @app.errorhandler(pg_errors.DeadlockDetected)
    def concurrency_conflict(e):
        return jsonify({"error": "Concurrent update conflict, please retry"}), 409

    @app.errorhandler(psycopg.OperationalError)   # also covers psycopg_pool.PoolTimeout
    def db_unavailable(e):
        return jsonify({"error": "Database unavailable"}), 503

    @app.errorhandler(HTTPException)                # Flask's own 404 / 405 as JSON
    def http_error(e):
        return jsonify({"error": e.description}), e.code