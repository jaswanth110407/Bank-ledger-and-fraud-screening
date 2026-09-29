"""
routes/auth.py
──────────────
Login and logout for both customers and bank officers.
Uses Werkzeug password hashing; sessions are server-side Flask sessions.
"""

from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, current_app)
from werkzeug.security import check_password_hash

from database import execute_query
from routes.utils import log_audit

auth_bp = Blueprint("auth", __name__)

DEMO_CUSTOMER_USERNAME = "arjun.mehta@demo.bank"
DEMO_CUSTOMER_PASSWORD = "demo1234"


# ─────────────────────────────────────────────────────────────────────────────
# GET / POST  /login
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["GET", "POST"])
@auth_bp.route("/customer/login", methods=["GET", "POST"])
def login():
    return _login_for_role("customer")


@auth_bp.route("/officer/login", methods=["GET", "POST"])
def officer_login():
    return _login_for_role("officer")


def _login_for_role(required_role: str):
    # Already logged in → bounce to correct dashboard
    if "user_id" in session:
        return _redirect_by_role(session["role"])

    if request.method == "GET":
        return render_template("login.html", login_role=required_role)

    # ── Validate form ──────────────────────────────────────────────────────
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        flash("Please enter both username and password.", "warning")
        return render_template("login.html", login_role=required_role), 400

    # Temporary offline demo: local-only, synthetic, read-only customer access.
    # This deliberately does not create an officer account or enable transfers.
    if (
        current_app.config.get("TEMP_DEMO_LOGIN_ENABLED", False)
        and request.remote_addr in {"127.0.0.1", "::1", "localhost"}
    ):
        demo_credentials = {
            "customer": (DEMO_CUSTOMER_USERNAME, DEMO_CUSTOMER_PASSWORD),
            "officer": ("officer1", "officer123"),
        }
        demo_username, demo_password = demo_credentials[required_role]
        if username == demo_username and password == demo_password:
            session.permanent = True
            session["user_id"] = 0
            session["username"] = demo_username
            session["role"] = required_role
            session["demo_mode"] = True
            if required_role == "customer":
                session["customer_name"] = "Arjun Mehta (Demo)"
                session["customer_id"] = 0
                session["account_id"] = 0
                session["account_number"] = "ACC1001"
                flash("Temporary offline demo: synthetic data only; transfers are disabled.", "info")
            else:
                flash("Temporary offline officer preview: synthetic data only; decisions are disabled.", "info")
            return _redirect_by_role(required_role)

    # ── Look up user (parameterised to prevent SQL injection) ──────────────
    try:
        user = execute_query(
            "SELECT * FROM users WHERE username = %s AND is_active = 1",
            (username,),
            fetch="one",
        )
    except Exception:
        current_app.logger.exception("Login database query failed")
        flash("Sign-in service is unavailable. Start MySQL or use the local demo account.", "danger")
        return render_template("login.html", login_role=required_role), 503

    if user is None or not check_password_hash(user["password_hash"], password):
        flash("Invalid credentials. Please try again.", "danger")
        return render_template("login.html", login_role=required_role), 401

    if user["role"] != required_role:
        flash(f"Invalid {required_role} credentials. Please try again.", "danger")
        return render_template("login.html", login_role=required_role), 401

    # ── Establish session ──────────────────────────────────────────────────
    session.permanent  = True
    session["user_id"] = user["user_id"]
    session["username"]= user["username"]
    session["role"]    = user["role"]

    # If customer, also store account info for quick access
    if user["role"] == "customer":
        acct = execute_query(
            """
            SELECT a.account_id, a.account_number, a.balance,
                   c.name, c.email, c.phone, c.customer_id
            FROM   accounts  a
            JOIN   customers c ON c.customer_id = a.customer_id
            JOIN   users     u ON u.user_id = %s
                                AND u.username = c.email
            WHERE  a.status = 'active'
            LIMIT  1
            """,
            (user["user_id"],),
            fetch="one",
        )
        if acct:
            session["account_id"]     = acct["account_id"]
            session["account_number"] = acct["account_number"]
            session["customer_name"]  = acct["name"]
            session["customer_id"]    = acct["customer_id"]

    log_audit(user["user_id"], "LOGIN", remarks=f"User '{username}' logged in")
    return _redirect_by_role(user["role"])


# ─────────────────────────────────────────────────────────────────────────────
# GET  /logout
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/logout")
def logout():
    user_id  = session.get("user_id")
    username = session.get("username", "unknown")

    if user_id and not session.get("demo_mode"):
        log_audit(user_id, "LOGOUT", remarks=f"User '{username}' logged out")

    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))


# ─────────────────────────────────────────────────────────────────────────────
# Root redirect
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/")
def index():
    if "user_id" in session:
        return _redirect_by_role(session["role"])
    return redirect(url_for("auth.login"))


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────
def _redirect_by_role(role: str):
    if role == "officer":
        return redirect(url_for("officer.dashboard"))
    return redirect(url_for("customer.dashboard"))
