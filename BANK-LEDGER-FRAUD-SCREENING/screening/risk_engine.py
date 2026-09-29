"""
screening/risk_engine.py
────────────────────────
Orchestrates all fraud rules, accumulates a risk score, assigns a risk level,
persists the screening result, and returns a structured result dict.

Disclaimer: Scores and thresholds are project-defined demonstration rules
and are NOT official banking or regulatory standards.
"""

import json
from datetime import datetime

from config import Config
from database import execute_query
from screening.fraud_rules import (
    rule_unusual_amount,
    rule_high_frequency,
    rule_new_recipient,
    rule_unusual_pattern,
)


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def screen_transaction(transaction_id: int,
                        sender_account: str,
                        receiver_account: str,
                        amount: float) -> dict:
    """
    Run all four fraud rules against a newly created transaction.

    Returns a dict:
    {
        "risk_score"       : int,
        "risk_level"       : "LOW" | "MEDIUM" | "HIGH",
        "triggered_signals": [ "Human-readable reason", ... ],
        "should_review"    : bool,   # True  → route to UNDER_REVIEW
    }

    Side-effects: inserts a row into screening_results.
    """
    score   = 0
    signals = []

    # ── Rule 1: Unusual Amount ─────────────────────────────────────────────
    triggered, reason = rule_unusual_amount(sender_account, amount, transaction_id)
    if triggered:
        score  += Config.SCORE_UNUSUAL_AMOUNT
        signals.append(f"Unusual amount – {reason}")

    # ── Rule 2: High Frequency ─────────────────────────────────────────────
    triggered, reason = rule_high_frequency(sender_account, transaction_id)
    if triggered:
        score  += Config.SCORE_HIGH_FREQUENCY
        signals.append(f"High transaction frequency – {reason}")

    # ── Rule 3: New Recipient ──────────────────────────────────────────────
    triggered, reason = rule_new_recipient(sender_account, receiver_account)
    if triggered:
        score  += Config.SCORE_NEW_RECIPIENT
        signals.append(f"New recipient – {reason}")

    # ── Rule 4: Unusual Pattern ────────────────────────────────────────────
    triggered, reason = rule_unusual_pattern(sender_account, amount, transaction_id)
    if triggered:
        score  += Config.SCORE_UNUSUAL_PATTERN
        signals.append(f"Unusual pattern – {reason}")

    # Cap at 100
    score = min(score, 100)

    # ── Determine risk level ───────────────────────────────────────────────
    if score <= Config.RISK_LOW_MAX:
        risk_level = "LOW"
    elif score <= Config.RISK_MEDIUM_MAX:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    should_review = score >= Config.AUTO_REVIEW_THRESHOLD

    # ── Persist screening result ───────────────────────────────────────────
    _save_screening_result(transaction_id, score, risk_level, signals)

    return {
        "risk_score"       : score,
        "risk_level"       : risk_level,
        "triggered_signals": signals,
        "should_review"    : should_review,
    }


def get_screening_result(transaction_id: int) -> dict | None:
    """Fetch the most recent screening result for a transaction."""
    row = execute_query(
        "SELECT * FROM screening_results WHERE transaction_id = %s "
        "ORDER BY screened_at DESC LIMIT 1",
        (transaction_id,),
        fetch="one",
    )
    if not row:
        return None

    # triggered_signals is stored as JSON text
    raw = row.get("triggered_signals", "[]")
    if isinstance(raw, str):
        try:
            row["triggered_signals"] = json.loads(raw)
        except json.JSONDecodeError:
            row["triggered_signals"] = []
    return row


# ──────────────────────────────────────────────────────────────────────────────
# Internal helper
# ──────────────────────────────────────────────────────────────────────────────

def _save_screening_result(transaction_id: int,
                             risk_score: int,
                             risk_level: str,
                             signals: list[str]) -> None:
    execute_query(
        """
        INSERT INTO screening_results
            (transaction_id, risk_score, risk_level, triggered_signals, screened_at)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (transaction_id, risk_score, risk_level,
         json.dumps(signals), datetime.utcnow()),
        fetch="none",
    )
