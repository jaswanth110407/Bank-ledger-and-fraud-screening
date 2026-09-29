"""
routes/transactions.py
──────────────────────
Fund-transfer endpoint: validates input, creates a ledger entry,
runs automated fraud screening, and routes the transaction.
"""

import uuid
from datetime import datetime
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, jsonify)

from database import execute_query
from routes.utils import customer_required, log_audit
from screening.risk_engine import screen_transaction

transactions_bp = Blueprint("transactions", __name__, url_prefix="/transfer")

VALID_TYPES = {"NEFT", "RTGS", "IMPS", "UPI"}


# ─────────────────────────────────────────────────────────────────────────────
# GET/POST  /transfer/
# ─────────────────────────────────────────────────────────────────────────────
@transactions_bp.route("/", methods=["GET", "POST"])
@customer_required
def transfer():
    if session.get("demo_mode"):
        flash("Transfers are disabled in the temporary offline demo.", "warning")
        return redirect(url_for("customer.dashboard"))

    acct_no = session.get("account_number")
    acct_id = session.get("account_id")

    if request.method == "GET":
        # Pass fresh balance
        acct = execute_query(
            "SELECT balance FROM accounts WHERE account_id = %s",
            (acct_id,), fetch="one"
        )
        return render_template("transfer.html", acct=acct)

    # ── Collect & sanitise form data ───────────────────────────────────────
    receiver = request.form.get("receiver_account", "").strip().upper()
    raw_amt  = request.form.get("amount", "").strip()
    tx_type  = request.form.get("transaction_type", "NEFT").strip().upper()
    remarks  = request.form.get("remarks", "").strip()[:200]

    errors = []

    # Amount validation
    try:
        amount = float(raw_amt)
        if amount <= 0:
            errors.append("Amount must be greater than ₹0.")
    except ValueError:
        amount = None
        errors.append("Please enter a valid numeric amount.")

    if not receiver:
        errors.append("Receiver account number is required.")

    if tx_type not in VALID_TYPES:
        tx_type = "NEFT"

    if errors:
        acct = execute_query(
            "SELECT balance FROM accounts WHERE account_id = %s",
            (acct_id,), fetch="one"
        )
        for e in errors:
            flash(e, "danger")
        return render_template("transfer.html", acct=acct), 400

    # ── Check receiver account exists ──────────────────────────────────────
    recv_acct = execute_query(
        "SELECT * FROM accounts WHERE account_number = %s AND status = 'active'",
        (receiver,), fetch="one"
    )
    if not recv_acct:
        flash("Receiver account not found or inactive.", "danger")
        acct = execute_query(
            "SELECT balance FROM accounts WHERE account_id = %s",
            (acct_id,), fetch="one"
        )
        return render_template("transfer.html", acct=acct), 400

    # ── Can't send to self ─────────────────────────────────────────────────
    if receiver == acct_no:
        flash("You cannot transfer funds to your own account.", "warning")
        acct = execute_query(
            "SELECT balance FROM accounts WHERE account_id = %s",
            (acct_id,), fetch="one"
        )
        return render_template("transfer.html", acct=acct), 400

    # ── Sufficient balance check ───────────────────────────────────────────
    sender_acct = execute_query(
        "SELECT balance FROM accounts WHERE account_id = %s",
        (acct_id,), fetch="one"
    )
    if float(sender_acct["balance"]) < amount:
        flash("Insufficient balance.", "danger")
        return render_template("transfer.html", acct=sender_acct), 400

    # ── Create transaction record ──────────────────────────────────────────
    ref_no = f"REF{uuid.uuid4().hex[:10].upper()}"
    tx_id  = execute_query(
        """
        INSERT INTO transactions
            (sender_account, receiver_account, amount, transaction_type,
             transaction_time, reference_number, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'PENDING')
        """,
        (acct_no, receiver, amount, tx_type, datetime.utcnow(), ref_no),
        fetch="none",
    )

    log_audit(session["user_id"], "TRANSACTION_CREATED",
              transaction_id=tx_id,
              remarks=f"Transfer ₹{amount:,.2f} → {receiver}")

    # ── Run automated screening ────────────────────────────────────────────
    result = screen_transaction(tx_id, acct_no, receiver, amount)

    log_audit(session["user_id"], "SCREENING_COMPLETE",
              transaction_id=tx_id,
              remarks=f"Risk={result['risk_level']} Score={result['risk_score']}")

    # ── Determine status & update balance ──────────────────────────────────
    if result["should_review"]:
        new_status = "UNDER_REVIEW"
    else:
        new_status = "APPROVED"
        # Debit sender, credit receiver (only for approved)
        execute_query(
            "UPDATE accounts SET balance = balance - %s WHERE account_number = %s",
            (amount, acct_no), fetch="none"
        )
        execute_query(
            "UPDATE accounts SET balance = balance + %s WHERE account_number = %s",
            (amount, receiver), fetch="none"
        )

    execute_query(
        "UPDATE transactions SET status = %s WHERE transaction_id = %s",
        (new_status, tx_id), fetch="none"
    )

    log_audit(session["user_id"], "TRANSACTION_STATUS_UPDATED",
              transaction_id=tx_id, remarks=f"Status → {new_status}")

    # ── Redirect with outcome flash ────────────────────────────────────────
    if new_status == "APPROVED":
        flash(
            f"Transfer of ₹{amount:,.2f} to {receiver} completed successfully. "
            f"Reference: {ref_no}",
            "success"
        )
    else:
        flash(
            f"Your transfer (₹{amount:,.2f} to {receiver}) has been flagged for "
            f"review (Risk Level: {result['risk_level']}). Reference: {ref_no}",
            "warning"
        )

    return redirect(url_for("customer.dashboard"))


# ─────────────────────────────────────────────────────────────────────────────
# GET  /transfer/status/<tx_id>   – JSON API for status polling
# ─────────────────────────────────────────────────────────────────────────────
@transactions_bp.route("/status/<int:tx_id>")
@customer_required
def status(tx_id: int):
    if session.get("demo_mode"):
        return jsonify({"error": "Demo transactions are read-only"}), 404

    acct_no = session.get("account_number")
    tx = execute_query(
        "SELECT * FROM transactions WHERE transaction_id = %s "
        "AND (sender_account = %s OR receiver_account = %s)",
        (tx_id, acct_no, acct_no), fetch="one"
    )
    if not tx:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"status": tx["status"]})
