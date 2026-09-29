"""
screening/fraud_rules.py
────────────────────────
Individual rule functions for the automated first-level screening engine.

Each rule receives a context dict and returns a (triggered: bool, reason: str).

NOTE: All thresholds come from config.py and are labelled as
      "project-defined demonstration rules" – they are NOT official
      banking or regulatory standards.
"""

import statistics
from datetime import datetime, timedelta
from config import Config
from database import execute_query


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _recent_amounts(sender_account: str, exclude_tx_id: int = None) -> list[float]:
    """
    Return a list of amounts from previous COMPLETED transactions sent
    by sender_account (excluding the current in-flight transaction).
    """
    sql = """
        SELECT t.amount
        FROM   transactions t
        WHERE  t.sender_account = %s
          AND  t.status NOT IN ('REJECTED')
          AND  (%s IS NULL OR t.transaction_id != %s)
        ORDER BY t.transaction_time DESC
        LIMIT 50
    """
    rows = execute_query(sql, (sender_account, exclude_tx_id, exclude_tx_id))
    return [float(r["amount"]) for r in rows]


def _recent_tx_count_in_window(sender_account: str,
                                window_minutes: int,
                                exclude_tx_id: int = None) -> int:
    """Count how many transactions the sender has made in the last N minutes."""
    cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
    sql = """
        SELECT COUNT(*) AS cnt
        FROM   transactions
        WHERE  sender_account = %s
          AND  transaction_time >= %s
          AND  (%s IS NULL OR transaction_id != %s)
    """
    row = execute_query(sql, (sender_account, cutoff, exclude_tx_id, exclude_tx_id), fetch="one")
    return int(row["cnt"]) if row else 0


def _has_prior_transfer(sender_account: str, receiver_account: str) -> bool:
    """Return True if sender has EVER transferred to this receiver before."""
    sql = """
        SELECT COUNT(*) AS cnt
        FROM   transactions
        WHERE  sender_account   = %s
          AND  receiver_account = %s
          AND  status NOT IN ('REJECTED')
    """
    row = execute_query(sql, (sender_account, receiver_account), fetch="one")
    return int(row["cnt"]) > 0 if row else False


# ──────────────────────────────────────────────────────────────────────────────
# Rule 1 – Unusual Amount
# ──────────────────────────────────────────────────────────────────────────────

def rule_unusual_amount(sender_account: str,
                         amount: float,
                         exclude_tx_id: int = None) -> tuple[bool, str]:
    """
    FLAG if the transaction amount is significantly higher than the sender's
    historical average (mean × UNUSUAL_AMOUNT_MULTIPLIER).

    Requires at least UNUSUAL_AMOUNT_MIN_SAMPLES prior transactions.
    """
    history = _recent_amounts(sender_account, exclude_tx_id)

    if len(history) < Config.UNUSUAL_AMOUNT_MIN_SAMPLES:
        return False, ""    # Not enough data to evaluate

    avg = statistics.mean(history)
    threshold = avg * Config.UNUSUAL_AMOUNT_MULTIPLIER

    if amount > threshold:
        return (
            True,
            f"Amount ₹{amount:,.2f} is {amount/avg:.1f}× your typical "
            f"average of ₹{avg:,.2f} (threshold: {Config.UNUSUAL_AMOUNT_MULTIPLIER}×)"
        )
    return False, ""


# ──────────────────────────────────────────────────────────────────────────────
# Rule 2 – High Transaction Frequency
# ──────────────────────────────────────────────────────────────────────────────

def rule_high_frequency(sender_account: str,
                          exclude_tx_id: int = None) -> tuple[bool, str]:
    """
    FLAG if the sender has exceeded FREQ_MAX_TXN transactions within
    the last FREQ_WINDOW_MINUTES minutes.
    """
    count = _recent_tx_count_in_window(
        sender_account, Config.FREQ_WINDOW_MINUTES, exclude_tx_id
    )

    if count >= Config.FREQ_MAX_TXN:
        return (
            True,
            f"{count} transactions in the last {Config.FREQ_WINDOW_MINUTES} min "
            f"(limit: {Config.FREQ_MAX_TXN})"
        )
    return False, ""


# ──────────────────────────────────────────────────────────────────────────────
# Rule 3 – New Recipient
# ──────────────────────────────────────────────────────────────────────────────

def rule_new_recipient(sender_account: str,
                        receiver_account: str) -> tuple[bool, str]:
    """
    FLAG if this is the FIRST transfer from sender to this specific receiver.
    """
    if not _has_prior_transfer(sender_account, receiver_account):
        return True, f"First-ever transfer to account {receiver_account}"
    return False, ""


# ──────────────────────────────────────────────────────────────────────────────
# Rule 4 – Unusual Pattern (statistical deviation)
# ──────────────────────────────────────────────────────────────────────────────

def rule_unusual_pattern(sender_account: str,
                           amount: float,
                           exclude_tx_id: int = None) -> tuple[bool, str]:
    """
    FLAG if the transaction amount is more than PATTERN_STD_MULTIPLIER
    standard deviations above the sender's mean (Z-score check).

    Requires at least PATTERN_MIN_SAMPLES prior transactions.
    """
    history = _recent_amounts(sender_account, exclude_tx_id)

    if len(history) < Config.PATTERN_MIN_SAMPLES:
        return False, ""

    mean = statistics.mean(history)
    try:
        stdev = statistics.stdev(history)
    except statistics.StatisticsError:
        return False, ""

    if stdev == 0:
        return False, ""    # All historical amounts are identical – no pattern deviation

    z_score = (amount - mean) / stdev

    if z_score > Config.PATTERN_STD_MULTIPLIER:
        return (
            True,
            f"Transaction is {z_score:.1f} standard deviations above your "
            f"historical mean (threshold: {Config.PATTERN_STD_MULTIPLIER}σ)"
        )
    return False, ""
