"""Flask app factory.  Run with:  flask --app app run   (Flask finds create_app automatically)"""
from flask import Flask

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
    return app