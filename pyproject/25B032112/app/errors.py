"""JSON error responses. Step 5 adds the psycopg exception handlers."""
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
    @app.errorhandler(ApiError)
    def api_error(e):
        return jsonify({"error": e.message}), e.status

    @app.errorhandler(pg_errors.CheckViolation)      # e.g. balance would go below 0
    def check_violation(e):
        return jsonify({"error": "Constraint check failed", "constraint": e.diag.constraint_name}), 400

    @app.errorhandler(HTTPException)                 # Flask's own 404 / 405 as JSON
    def http_error(e):
        return jsonify({"error": e.description}), e.code