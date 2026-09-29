"""
routes/utils.py
───────────────
Shared helpers: decorators, audit logging, formatting.
"""

from functools import wraps
from types import SimpleNamespace
from flask import session, redirect, url_for, flash
from database import execute_query
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# Access-control decorators
# ─────────────────────────────────────────────────────────────────────────────

def login_required(f):
    """Redirect unauthenticated users to the login page."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def officer_required(f):
    """Allow only users with role='officer'."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        if session.get("role") != "officer":
            flash("Access denied – officer accounts only.", "danger")
            return redirect(url_for("customer.dashboard"))
        return f(*args, **kwargs)
    return decorated


def customer_required(f):
    """Allow only users with role='customer'."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        if session.get("role") != "customer":
            flash("Access denied – customer accounts only.", "danger")
            return redirect(url_for("officer.dashboard"))
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────────────────────────────────────
# Audit logging
# ─────────────────────────────────────────────────────────────────────────────

def log_audit(user_id: int,
              action: str,
              transaction_id: int = None,
              remarks: str = "") -> None:
    """Insert a row into audit_logs. Silently ignores DB errors."""
    try:
        execute_query(
            """
            INSERT INTO audit_logs
                (user_id, action, transaction_id, remarks, timestamp)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, action, transaction_id, remarks, datetime.utcnow()),
            fetch="none",
        )
    except Exception:
        pass    # Audit failures must never crash the main request


# ─────────────────────────────────────────────────────────────────────────────
# Pagination helper
# ─────────────────────────────────────────────────────────────────────────────

def paginate(query_result: list, page: int, per_page: int = 15) -> SimpleNamespace:
    total   = len(query_result)
    start   = (page - 1) * per_page
    end     = start + per_page
    pages   = (total + per_page - 1) // per_page
    return SimpleNamespace(
        items=query_result[start:end],
        total=total,
        page=page,
        pages=pages,
        per_page=per_page,
        has_prev=page > 1,
        has_next=page < pages,
    )
