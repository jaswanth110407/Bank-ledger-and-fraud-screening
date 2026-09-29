"""Synthetic read-only customer data for the temporary offline demo."""

from datetime import datetime, timedelta
from types import SimpleNamespace


_demo_now = datetime.now()

DEMO_ACCOUNT = {
    "account_id": 0,
    "customer_id": 0,
    "account_number": "ACC1001",
    "balance": 125000.00,
    "status": "active",
    "name": "Arjun Mehta",
    "email": "arjun.mehta@demo.bank",
    "phone": "+91-98001-11001",
    "cust_status": "active",
    "member_since": _demo_now - timedelta(days=365),
}

DEMO_TRANSACTIONS = [
    {
        "transaction_id": 9003,
        "sender_account": "ACC1001",
        "receiver_account": "ACC1003",
        "amount": 2500.00,
        "transaction_type": "UPI",
        "transaction_time": _demo_now - timedelta(hours=3),
        "reference_number": "DEMO-REF-9003",
        "risk_score": 10,
        "risk_level": "LOW",
        "status": "APPROVED",
    },
    {
        "transaction_id": 9002,
        "sender_account": "ACC1002",
        "receiver_account": "ACC1001",
        "amount": 7500.00,
        "transaction_type": "NEFT",
        "transaction_time": _demo_now - timedelta(days=1),
        "reference_number": "DEMO-REF-9002",
        "risk_score": 5,
        "risk_level": "LOW",
        "status": "APPROVED",
    },
    {
        "transaction_id": 9001,
        "sender_account": "ACC1001",
        "receiver_account": "ACC1004",
        "amount": 1200.00,
        "transaction_type": "IMPS",
        "transaction_time": _demo_now - timedelta(days=2),
        "reference_number": "DEMO-REF-9001",
        "risk_score": 15,
        "risk_level": "LOW",
        "status": "PENDING",
    },
]

DEMO_STATS = {
    "total": 3,
    "approved": 2,
    "pending": 1,
    "under_review": 0,
    "rejected": 0,
}

DEMO_OFFICER_TRANSACTIONS = DEMO_TRANSACTIONS + [
    {
        "transaction_id": 9004,
        "sender_account": "ACC1005",
        "receiver_account": "ACC1001",
        "amount": 80000.00,
        "transaction_type": "RTGS",
        "transaction_time": _demo_now - timedelta(minutes=35),
        "reference_number": "DEMO-REF-9004",
        "risk_score": 75,
        "risk_level": "HIGH",
        "triggered_signals": ["Unusual amount", "New recipient", "Unusual pattern"],
        "status": "UNDER_REVIEW",
    },
]

DEMO_OFFICER_STATS = SimpleNamespace(
    total=4,
    approved=2,
    pending=1,
    under_review=1,
    rejected=0,
    held=0,
)

DEMO_RISK_DISTRIBUTION = {"LOW": 2, "MEDIUM": 1, "HIGH": 1}

DEMO_REVIEW_AUDIT_LOGS = [
    SimpleNamespace(
        review_id=125,
        transaction_id=125,
        officer_id=102,
        decision="HOLD",
        remarks="Requires additional verification",
        reviewed_at=_demo_now.replace(hour=10, minute=42, second=0, microsecond=0),
    ),
    SimpleNamespace(
        review_id=124,
        transaction_id=124,
        officer_id=101,
        decision="APPROVE",
        remarks="Customer confirmed the transfer through the registered channel",
        reviewed_at=_demo_now - timedelta(hours=2),
    ),
    SimpleNamespace(
        review_id=123,
        transaction_id=123,
        officer_id=102,
        decision="REJECT",
        remarks="Recipient details did not match the verification records",
        reviewed_at=_demo_now - timedelta(days=1, minutes=18),
    ),
    SimpleNamespace(
        review_id=122,
        transaction_id=122,
        officer_id=101,
        decision="HOLD",
        remarks="Unusual transfer pattern referred for secondary review",
        reviewed_at=_demo_now - timedelta(days=2, minutes=35),
    ),
]
