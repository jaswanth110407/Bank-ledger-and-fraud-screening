"""
app.py – Application entry point
Registers blueprints and sets up database teardown hooks.
"""

from flask import Flask, render_template
from config import Config
from database import close_db

# ── Blueprints ────────────────────────────────────────────────────────────────
from routes.auth         import auth_bp
from routes.customer     import customer_bp
from routes.transactions import transactions_bp
from routes.officer      import officer_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # ── Database ──────────────────────────────────────────────────────────
    # The connection pool is created lazily by database.get_db() on the first
    # database request so the login page can load while MySQL is unavailable.
    app.teardown_appcontext(close_db)

    # ── Blueprints ────────────────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(officer_bp)

    # ── Custom error pages ────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404,
                               message="Page not found."), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403,
                               message="Access denied."), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template("error.html", code=500,
                               message="Internal server error."), 500

    # ── Jinja2 global helpers ──────────────────────────────────────────────
    @app.template_filter("inr")
    def inr_format(value):
        """Format a number as Indian Rupees with commas."""
        try:
            return f"₹{float(value):,.2f}"
        except (TypeError, ValueError):
            return "₹0.00"

    @app.template_filter("risk_badge")
    def risk_badge(level: str) -> str:
        colours = {"LOW": "success", "MEDIUM": "warning", "HIGH": "danger"}
        c = colours.get((level or "").upper(), "secondary")
        return f'<span class="badge bg-{c}">{level or "N/A"}</span>'

    @app.template_filter("status_badge")
    def status_badge(status: str) -> str:
        colours = {
            "APPROVED"    : "success",
            "PENDING"     : "warning",
            "UNDER_REVIEW": "info",
            "REJECTED"    : "danger",
            "HELD"        : "secondary",
        }
        c = colours.get((status or "").upper(), "secondary")
        return f'<span class="badge bg-{c} status-badge">{status or "N/A"}</span>'

    return app


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
