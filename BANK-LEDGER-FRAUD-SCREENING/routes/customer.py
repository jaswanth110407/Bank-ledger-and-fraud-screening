"""
routes/customer.py
──────────────────
Customer-facing pages: dashboard, ledger, transaction history, profile.
"""

from flask import Blueprint, render_template, session, request
from database import execute_query
from routes.utils import customer_required, paginate
from routes.demo_data import DEMO_ACCOUNT, DEMO_STATS, DEMO_TRANSACTIONS

customer_bp = Blueprint("customer", __name__, url_prefix="/customer")


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────────────────
@customer_bp.route("/dashboard")
@customer_required
def dashboard():
    acct_no  = session.get("account_number")
    acct_id  = session.get("account_id")

    if session.get("demo_mode"):
        return render_template(
            "customer_dashboard.html",
            acct=DEMO_ACCOUNT,
            recent=DEMO_TRANSACTIONS,
            stats=DEMO_STATS,
        )

    # Fresh balance
    acct = execute_query(
        "SELECT * FROM accounts WHERE account_id = %s", (acct_id,), fetch="one"
    )

    # Recent 10 transactions
    recent = execute_query(
        """
        SELECT t.*, sr.risk_score, sr.risk_level
        FROM   transactions t
        LEFT JOIN screening_results sr ON sr.transaction_id = t.transaction_id
            AND sr.screening_id = (
                SELECT MAX(s2.screening_id) FROM screening_results s2
                WHERE s2.transaction_id = t.transaction_id
            )
        WHERE  t.sender_account = %s OR t.receiver_account = %s
        ORDER BY t.transaction_time DESC
        LIMIT  10
        """,
        (acct_no, acct_no),
    )

    # Stats
    stats = execute_query(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'APPROVED' THEN 1 ELSE 0 END)      AS approved,
            SUM(CASE WHEN status = 'PENDING'  THEN 1 ELSE 0 END)      AS pending,
            SUM(CASE WHEN status = 'UNDER_REVIEW' THEN 1 ELSE 0 END)  AS under_review,
            SUM(CASE WHEN status = 'REJECTED' THEN 1 ELSE 0 END)      AS rejected
        FROM   transactions
        WHERE  sender_account = %s OR receiver_account = %s
        """,
        (acct_no, acct_no),
        fetch="one",
    )

    return render_template(
        "customer_dashboard.html",
        acct=acct,
        recent=recent,
        stats=stats,
    )


# ─────────────────────────────────────────────────────────────────────────────
# My Ledger (all transactions with search/filter/pagination)
# ─────────────────────────────────────────────────────────────────────────────
@customer_bp.route("/ledger")
@customer_required
def ledger():
    acct_no = session.get("account_number")
    page    = int(request.args.get("page", 1))
    status  = request.args.get("status", "").upper()
    search  = request.args.get("q", "").strip()

    if session.get("demo_mode"):
        rows = DEMO_TRANSACTIONS
        if status:
            rows = [tx for tx in rows if tx["status"] == status]
        if search:
            needle = search.lower()
            rows = [
                tx for tx in rows
                if needle in str(tx["transaction_id"]).lower()
                or needle in tx["sender_account"].lower()
                or needle in tx["receiver_account"].lower()
                or needle in tx["reference_number"].lower()
            ]
        return render_template(
            "ledger.html",
            paged=paginate(rows, page),
            status_filter=status,
            search=search,
            role="customer",
        )

    where_clauses = ["(t.sender_account = %s OR t.receiver_account = %s)"]
    params        = [acct_no, acct_no]

    if status:
        where_clauses.append("t.status = %s")
        params.append(status)
    if search:
        where_clauses.append(
            "(t.transaction_id LIKE %s OR t.receiver_account LIKE %s "
            "OR t.reference_number LIKE %s)"
        )
        like = f"%{search}%"
        params += [like, like, like]

    where = " AND ".join(where_clauses)
    rows = execute_query(
        f"""
        SELECT t.*,
               sr.risk_score, sr.risk_level, sr.triggered_signals
        FROM   transactions t
        LEFT JOIN screening_results sr ON sr.transaction_id = t.transaction_id
            AND sr.screening_id = (
                SELECT MAX(s2.screening_id) FROM screening_results s2
                WHERE s2.transaction_id = t.transaction_id
            )
        WHERE  {where}
        ORDER BY t.transaction_time DESC
        """,
        tuple(params),
    )

    paged = paginate(rows, page)
    return render_template(
        "ledger.html",
        paged=paged,
        status_filter=status,
        search=search,
        role="customer",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Transaction History (alias / simplified view)
# ─────────────────────────────────────────────────────────────────────────────
@customer_bp.route("/history")
@customer_required
def history():
    acct_no = session.get("account_number")
    page    = int(request.args.get("page", 1))

    if session.get("demo_mode"):
        rows = [
            tx for tx in DEMO_TRANSACTIONS
            if tx["sender_account"] == session.get("account_number")
        ]
        return render_template(
            "transaction_history.html",
            paged=paginate(rows, page),
        )

    rows = execute_query(
        """
        SELECT t.*,
               sr.risk_score, sr.risk_level
        FROM   transactions t
        LEFT JOIN screening_results sr ON sr.transaction_id = t.transaction_id
            AND sr.screening_id = (
                SELECT MAX(s2.screening_id) FROM screening_results s2
                WHERE s2.transaction_id = t.transaction_id
            )
        WHERE  t.sender_account = %s
        ORDER BY t.transaction_time DESC
        """,
        (acct_no,),
    )
    paged = paginate(rows, page)
    return render_template("transaction_history.html", paged=paged)


# ─────────────────────────────────────────────────────────────────────────────
# Profile
# ─────────────────────────────────────────────────────────────────────────────
@customer_bp.route("/profile")
@customer_required
def profile():
    acct_id = session.get("account_id")
    if session.get("demo_mode"):
        return render_template("profile.html", acct=DEMO_ACCOUNT)

    acct = execute_query(
        """
        SELECT a.*, c.name, c.email, c.phone, c.status AS cust_status, c.created_at AS member_since
        FROM   accounts  a
        JOIN   customers c ON c.customer_id = a.customer_id
        WHERE  a.account_id = %s
        """,
        (acct_id,),
        fetch="one",
    )
    return render_template("profile.html", acct=acct)
