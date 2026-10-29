"""Flask app factory.  Run with:  flask --app app run   (Flask finds create_app automatically)"""
from flask import Flask, jsonify

from app.db import pool
from app.errors import register_error_handlers


def create_app():
    app = Flask(__name__)

    from app.routes.customers import bp as customers_bp
    from app.routes.accounts import bp as accounts_bp
    from app.routes.transactions import bp as transactions_bp

    app.register_blueprint(customers_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(transactions_bp)
    register_error_handlers(app)

    @app.route("/health")
    def health():
        pool.check()       # drops broken connections and refills the pool; it does NOT raise
        try:
            with pool.connection(timeout=2) as conn:   # so prove the DB answers with a real query
                conn.execute("SELECT 1")
        except Exception as e:
            return jsonify({"status": "error", "detail": str(e), "pool": pool.get_stats()}), 503
        return jsonify({"status": "ok", "pool": pool.get_stats()})

    return app