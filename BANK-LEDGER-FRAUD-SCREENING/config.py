"""
config.py – Application configuration
Loads settings from .env; never hard-codes credentials.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()   # reads .env if present


class Config:
    # ── Flask core ────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-fallback-secret-change-me!")
    FLASK_ENV: str  = os.getenv("FLASK_ENV", "development")
    DEBUG: bool     = os.getenv("FLASK_DEBUG", "1") == "1"
    TEMP_DEMO_LOGIN_ENABLED: bool = os.getenv(
        "TEMP_DEMO_LOGIN_ENABLED", "1" if DEBUG else "0"
    ) == "1"

    # ── Session ───────────────────────────────────────────────
    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=int(os.getenv("SESSION_LIFETIME_MINUTES", 30))
    )

    # ── Database ──────────────────────────────────────────────
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 3306))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "bank_screening")

    # ── Fraud-screening thresholds (easily tunable) ───────────
    # Rule 1 – Unusual amount: flag if tx > UNUSUAL_AMOUNT_MULTIPLIER × sender avg
    UNUSUAL_AMOUNT_MULTIPLIER: float = 3.0
    UNUSUAL_AMOUNT_MIN_SAMPLES: int  = 3     # need at least N prior txns

    # Rule 2 – High frequency: flag if > MAX_TXN_IN_WINDOW within WINDOW_MINUTES
    FREQ_MAX_TXN: int       = 5
    FREQ_WINDOW_MINUTES: int = 60

    # Rule 3 – New recipient (no prior transfer to this account)
    # (boolean – no threshold needed)

    # Rule 4 – Unusual pattern: flag if > PATTERN_STD_MULTIPLIER stddev from mean
    PATTERN_STD_MULTIPLIER: float = 2.0
    PATTERN_MIN_SAMPLES: int      = 3

    # ── Risk score weights ────────────────────────────────────
    SCORE_UNUSUAL_AMOUNT: int   = 30
    SCORE_HIGH_FREQUENCY: int   = 20
    SCORE_NEW_RECIPIENT: int    = 15
    SCORE_UNUSUAL_PATTERN: int  = 20

    # ── Risk level thresholds ─────────────────────────────────
    RISK_LOW_MAX: int    = 29    # 0-29   → LOW
    RISK_MEDIUM_MAX: int = 59    # 30-59  → MEDIUM
    # 60-100 → HIGH

    # ── Review routing ────────────────────────────────────────
    # Transactions with risk_score >= AUTO_REVIEW_THRESHOLD go to UNDER_REVIEW
    AUTO_REVIEW_THRESHOLD: int = 30
