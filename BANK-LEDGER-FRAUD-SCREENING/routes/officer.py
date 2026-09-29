"""
routes/officer.py
─────────────────
Bank officer routes: dashboard, full ledger, review queue, transaction details,
approve/reject/hold actions, and audit log viewer.
"""

import json
from types import SimpleNamespace
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash)

from database import execute_query
from routes.utils import officer_required, log_audit, paginate
from screening.risk_engine import get_screening_result
from routes.demo_data import (
    DEMO_REVIEW_AUDIT_LOGS,
    DEMO_OFFICER_STATS,
    DEMO_OFFICER_TRANSACTIONS,
    DEMO_RISK_DISTRIBUTION,
)

officer_bp = Blueprint("officer", __name__, url_prefix="/officer")


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────────────────
@officer_bp.route("/dashboard")
@officer_required
def dashboard():
    if session.get("demo_mode"):
        pending_reviews = [
            tx for tx in DEMO_OFFICER_TRANSACTIONS
            if tx["status"] == "UNDER_REVIEW"
        ]
        return render_template(
            "officer_dashboard.html",
            stats=DEMO_OFFICER_STATS,
            high_risk=1,
            recent=DEMO_OFFICER_TRANSACTIONS,
            pending_reviews=pending_reviews,
            risk_dist=DEMO_RISK_DISTRIBUTION,
        )

    # KPI cards
    stats = execute_query(
        """
        SELECT
            COUNT(*)                                                        AS total,
            SUM(CASE WHEN status = 'APPROVED'     THEN 1 ELSE 0 END)       AS approved,
            SUM(CASE WHEN status = 'PENDING'      THEN 1 ELSE 0 END)       AS pending,
            SUM(CASE WHEN status = 'UNDER_REVIEW' THEN 1 ELSE 0 END)       AS under_review,
            SUM(CASE WHEN status = 'REJECTED'     THEN 1 ELSE 0 END)       AS rejected,
            SUM(CASE WHEN status = 'HELD'         THEN 1 ELSE 0 END)       AS held
        FROM transactions
        """,
        fetch="one",
    )

    # High-risk count
    high_risk = execute_query(
        """
        SELECT COUNT(*) AS cnt FROM screening_results
        WHERE risk_level = 'HIGH'
          AND screening_id IN (
              SELECT MAX(screening_id) FROM screening_results
              GROUP BY transaction_id
          )
        """,
        fetch="one",
    )

    # Recent 10 transactions (all accounts)
    recent = execute_query(
        """
        SELECT t.*, sr.risk_score, sr.risk_level
        FROM   transactions t
        LEFT JOIN screening_results sr ON sr.transaction_id = t.transaction_id
            AND sr.screening_id = (
                SELECT MAX(s2.screening_id) FROM screening_results s2
                WHERE s2.transaction_id = t.transaction_id
            )
        ORDER BY t.transaction_time DESC
        LIMIT 10
        """,
    )

    # Pending reviews
    pending_reviews = execute_query(
        """
        SELECT t.*, sr.risk_score, sr.risk_level
        FROM   transactions t
        JOIN   screening_results sr ON sr.transaction_id = t.transaction_id
            AND sr.screening_id = (
                SELECT MAX(s2.screening_id) FROM screening_results s2
                WHERE s2.transaction_id = t.transaction_id
            )
        WHERE  t.status = 'UNDER_REVIEW'
        ORDER BY sr.risk_score DESC, t.transaction_time ASC
        LIMIT 5
        """,
    )

    # Risk level distribution
    risk_dist = execute_query(
        """
        SELECT sr.risk_level, COUNT(*) AS cnt
        FROM   screening_results sr
        WHERE  sr.screening_id IN (
            SELECT MAX(screening_id) FROM screening_results
            GROUP BY transaction_id
        )
        GROUP BY sr.risk_level
        """,
    )

    return render_template(
        "officer_dashboard.html",
        stats=stats,
        high_risk=high_risk["cnt"] if high_risk else 0,
        recent=recent,
        pending_reviews=pending_reviews,
        risk_dist={r["risk_level"]: r["cnt"] for r in risk_dist},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Full Ledger (all transactions, searchable/filterable)
# ─────────────────────────────────────────────────────────────────────────────
@officer_bp.route("/ledger")
@officer_required
def ledger():
    page       = int(request.args.get("page", 1))
    status     = request.args.get("status", "").upper()
    risk_level = request.args.get("risk", "").upper()
    search     = request.args.get("q", "").strip()

    if session.get("demo_mode"):
        rows = DEMO_OFFICER_TRANSACTIONS
        if status:
            rows = [tx for tx in rows if tx["status"] == status]
        if risk_level:
            rows = [tx for tx in rows if tx["risk_level"] == risk_level]
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
            risk_filter=risk_level,
            search=search,
            role="officer",
        )

    where_clauses = ["1=1"]
    params        = []

    if status:
        where_clauses.append("t.status = %s")
        params.append(status)
    if risk_level:
        where_clauses.append("sr.risk_level = %s")
        params.append(risk_level)
    if search:
        where_clauses.append(
            "(t.transaction_id LIKE %s OR t.sender_account LIKE %s "
            "OR t.receiver_account LIKE %s OR t.reference_number LIKE %s)"
        )
        like = f"%{search}%"
        params += [like, like, like, like]

    where = " AND ".join(where_clauses)
    rows = execute_query(
        f"""
        SELECT t.*, sr.risk_score, sr.risk_level, sr.triggered_signals
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
        risk_filter=risk_level,
        search=search,
        role="officer",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Review Queue (UNDER_REVIEW transactions)
# ─────────────────────────────────────────────────────────────────────────────
@officer_bp.route("/review-queue")
@officer_required
def review_queue():
    page = int(request.args.get("page", 1))
    if session.get("demo_mode"):
        rows = [
            tx for tx in DEMO_OFFICER_TRANSACTIONS
            if tx["status"] == "UNDER_REVIEW"
        ]
        return render_template("review_queue.html", paged=paginate(rows, page, per_page=10))

    rows = execute_query(
        """
        SELECT t.*, sr.risk_score, sr.risk_level, sr.triggered_signals, sr.screened_at
        FROM   transactions t
        JOIN   screening_results sr ON sr.transaction_id = t.transaction_id
            AND sr.screening_id = (
                SELECT MAX(s2.screening_id) FROM screening_results s2
                WHERE s2.transaction_id = t.transaction_id
            )
        WHERE  t.status = 'UNDER_REVIEW'
        ORDER BY sr.risk_score DESC, t.transaction_time ASC
        """,
    )
    paged = paginate(rows, page, per_page=10)
    return render_template("review_queue.html", paged=paged)


# ─────────────────────────────────────────────────────────────────────────────
# Transaction Detail + Officer Decision
# ─────────────────────────────────────────────────────────────────────────────
@officer_bp.route("/transaction/<int:tx_id>", methods=["GET", "POST"])
@officer_required
def transaction_detail(tx_id: int):
    if session.get("demo_mode"):
        tx = next(
            (item for item in DEMO_OFFICER_TRANSACTIONS if item["transaction_id"] == tx_id),
            None,
        )
        if not tx:
            flash("Demo transaction not found.", "danger")
            return redirect(url_for("officer.ledger"))
        if request.method == "POST":
            flash("Decisions are disabled in the temporary offline preview.", "warning")
            return redirect(url_for("officer.transaction_detail", tx_id=tx_id))
        screening = SimpleNamespace(
            risk_score=tx["risk_score"],
            risk_level=tx["risk_level"],
            triggered_signals=tx.get("triggered_signals", []),
            screened_at=tx["transaction_time"],
        )
        return render_template(
            "transaction_details.html",
            tx=SimpleNamespace(**tx),
            screening=screening,
            review=None,
        )

    tx = execute_query(
        "SELECT * FROM transactions WHERE transaction_id = %s",
        (tx_id,), fetch="one"
    )
    if not tx:
        flash("Transaction not found.", "danger")
        return redirect(url_for("officer.ledger"))

    screening = get_screening_result(tx_id)

    # Decode triggered_signals JSON if needed
    if screening:
        raw = screening.get("triggered_signals", [])
        if isinstance(raw, str):
            try:
                screening["triggered_signals"] = json.loads(raw)
            except Exception:
                screening["triggered_signals"] = []

    # Existing review (if any)
    review = execute_query(
        "SELECT * FROM manual_reviews WHERE transaction_id = %s ORDER BY reviewed_at DESC LIMIT 1",
        (tx_id,), fetch="one"
    )

    if request.method == "POST":
        decision = request.form.get("decision", "").upper()
        remarks  = request.form.get("remarks", "").strip()[:500]

        if decision not in ("APPROVE", "REJECT", "HOLD"):
            flash("Invalid decision.", "danger")
            return redirect(url_for("officer.transaction_detail", tx_id=tx_id))

        status_map = {"APPROVE": "APPROVED", "REJECT": "REJECTED", "HOLD": "HELD"}
        new_status = status_map[decision]

        # Save review
        execute_query(
            """
            INSERT INTO manual_reviews
                (transaction_id, officer_id, decision, remarks, reviewed_at)
            VALUES (%s, %s, %s, %s, NOW())
            """,
            (tx_id, session["user_id"], decision, remarks),
            fetch="none",
        )

        # Update transaction status
        execute_query(
            "UPDATE transactions SET status = %s WHERE transaction_id = %s",
            (new_status, tx_id), fetch="none"
        )

        # If APPROVED, move funds
        if new_status == "APPROVED":
            execute_query(
                "UPDATE accounts SET balance = balance - %s WHERE account_number = %s",
                (tx["amount"], tx["sender_account"]), fetch="none"
            )
            execute_query(
                "UPDATE accounts SET balance = balance + %s WHERE account_number = %s",
                (tx["amount"], tx["receiver_account"]), fetch="none"
            )

        log_audit(
            session["user_id"],
            f"OFFICER_{decision}",
            transaction_id=tx_id,
            remarks=remarks or f"Officer decision: {decision}",
        )

        flash(
            f"Transaction #{tx_id} has been {new_status.lower()}. "
            f"Audit trail updated.",
            "success" if new_status == "APPROVED" else
            "danger" if new_status == "REJECTED" else "warning",
        )
        return redirect(url_for("officer.review_queue"))

    return render_template(
        "transaction_details.html",
        tx=tx,
        screening=screening,
        review=review,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Audit Logs
# ─────────────────────────────────────────────────────────────────────────────
@officer_bp.route("/audit-logs")
@officer_required
def audit_logs():
    page   = int(request.args.get("page", 1))
    decision = request.args.get("decision", "").strip().upper()
    search = request.args.get("q", "").strip()

    if session.get("demo_mode"):
        rows = DEMO_REVIEW_AUDIT_LOGS
        if decision:
            rows = [row for row in rows if row.decision == decision]
        if search:
            needle = search.lower()
            rows = [
                row for row in rows
                if needle in f"REV{row.review_id:05d}".lower()
                or needle in f"TX{row.transaction_id:05d}".lower()
                or needle in f"OFF{row.officer_id:03d}".lower()
                or needle in row.decision.lower()
                or needle in row.remarks.lower()
            ]
        return render_template(
            "audit_logs.html",
            paged=paginate(rows, page, per_page=20),
            decision_filter=decision,
            search=search,
        )

    where_clauses = ["1=1"]
    params        = []

    if decision:
        where_clauses.append("mr.decision = %s")
        params.append(decision)
    if search:
        where_clauses.append(
            "(CAST(mr.review_id AS CHAR) LIKE %s "
            "OR CAST(mr.transaction_id AS CHAR) LIKE %s "
            "OR CAST(mr.officer_id AS CHAR) LIKE %s "
            "OR mr.decision LIKE %s OR mr.remarks LIKE %s)"
        )
        like = f"%{search}%"
        params += [like, like, like, like, like]

    where = " AND ".join(where_clauses)
    rows = execute_query(
        f"""
        SELECT mr.review_id, mr.transaction_id, mr.officer_id,
               mr.decision, mr.remarks, mr.reviewed_at
        FROM   manual_reviews mr
        WHERE  {where}
        ORDER BY mr.reviewed_at DESC, mr.review_id DESC
        """,
        tuple(params),
    )

    paged = paginate(rows, page, per_page=20)
    return render_template(
        "audit_logs.html",
        paged=paged,
        decision_filter=decision,
        search=search,
    )
