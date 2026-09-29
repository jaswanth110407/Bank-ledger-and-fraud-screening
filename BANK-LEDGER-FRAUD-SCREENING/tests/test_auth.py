"""Tests for role-specific customer and officer login portals."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Keep authentication tests independent of a running MySQL server.
sys.modules.setdefault("database", MagicMock())
sys.modules.setdefault("mysql", MagicMock())
sys.modules.setdefault("mysql.connector", MagicMock())
sys.modules.setdefault("mysql.connector.pooling", MagicMock())

from app import create_app
from werkzeug.security import generate_password_hash


class TestRoleSpecificLogin:
    def setup_method(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = self.app.test_client()

    def test_login_pages_show_only_their_role_demo_account(self):
        customer_page = self.client.get("/customer/login")
        officer_page = self.client.get("/officer/login")

        assert customer_page.status_code == 200
        assert b"arjun.mehta@demo.bank" in customer_page.data
        assert b"officer1" not in customer_page.data
        assert officer_page.status_code == 200
        assert b"officer1" in officer_page.data
        assert b"arjun.mehta@demo.bank" not in officer_page.data

    def test_customer_account_is_rejected_by_officer_login(self):
        user = {
            "user_id": 1,
            "username": "customer@demo.bank",
            "password_hash": generate_password_hash("demo1234"),
            "role": "customer",
        }
        with patch("routes.auth.execute_query", return_value=user), patch(
            "routes.auth.log_audit"
        ) as audit:
            response = self.client.post(
                "/officer/login",
                data={"username": user["username"], "password": "demo1234"},
            )

        assert response.status_code == 401
        assert b"Invalid officer credentials" in response.data
        assert not audit.called
        with self.client.session_transaction() as session:
            assert "user_id" not in session

    def test_officer_account_is_rejected_by_customer_login(self):
        user = {
            "user_id": 6,
            "username": "officer1",
            "password_hash": generate_password_hash("officer123"),
            "role": "officer",
        }
        with patch("routes.auth.execute_query", return_value=user), patch(
            "routes.auth.log_audit"
        ) as audit:
            response = self.client.post(
                "/customer/login",
                data={"username": user["username"], "password": "officer123"},
            )

        assert response.status_code == 401
        assert b"Invalid customer credentials" in response.data
        assert not audit.called
        with self.client.session_transaction() as session:
            assert "user_id" not in session

    def test_temporary_customer_demo_works_without_database(self):
        fail_if_database_is_used = AssertionError("offline demo must not query MySQL")
        with patch("routes.auth.execute_query", side_effect=fail_if_database_is_used), patch(
            "routes.customer.execute_query", side_effect=fail_if_database_is_used
        ), patch("routes.transactions.execute_query", side_effect=fail_if_database_is_used):
            response = self.client.post(
                "/customer/login",
                data={
                    "username": "arjun.mehta@demo.bank",
                    "password": "demo1234",
                },
                follow_redirects=True,
            )

            assert response.status_code == 200
            assert b"Arjun Mehta" in response.data
            assert b"125,000.00" in response.data
            assert b"Temporary offline demo" in response.data
            assert b"#9003" in response.data
            assert b"Make Transfer" not in response.data

            ledger_response = self.client.get("/customer/ledger")
            assert ledger_response.status_code == 200
            assert b"DEMO-REF-9003" in ledger_response.data
            for path in ("/customer/history", "/customer/profile"):
                assert self.client.get(path).status_code == 200

            transfer_response = self.client.get("/transfer/")
            assert transfer_response.status_code == 302
            assert transfer_response.headers["Location"].endswith("/customer/dashboard")

        with self.client.session_transaction() as session:
            assert session.get("demo_mode") is True
            assert session.get("role") == "customer"

    def test_temporary_officer_demo_works_without_database(self):
        fail_if_database_is_used = AssertionError("offline demo must not query MySQL")
        with patch("routes.auth.execute_query", side_effect=fail_if_database_is_used), patch(
            "routes.officer.execute_query", side_effect=fail_if_database_is_used
        ):
            response = self.client.post(
                "/officer/login",
                data={"username": "officer1", "password": "officer123"},
                follow_redirects=True,
            )

            assert response.status_code == 200
            assert b"Operations Dashboard" in response.data
            assert b"#9004" in response.data
            assert b"Temporary offline officer preview" in response.data

            queue = self.client.get("/officer/review-queue")
            assert queue.status_code == 200
            assert b"DEMO-REF-9004" in queue.data

            detail = self.client.get("/officer/transaction/9004")
            assert detail.status_code == 200
            assert b"Read-only Demo Preview" in detail.data
            assert b'<form method="POST" action="/officer/transaction/9004"' not in detail.data

            decision = self.client.post(
                "/officer/transaction/9004",
                data={"decision": "APPROVE", "remarks": "test"},
                follow_redirects=True,
            )
            assert b"decisions are disabled" in decision.data

        with self.client.session_transaction() as session:
            assert session.get("demo_mode") is True
            assert session.get("role") == "officer"

    def test_database_outage_shows_friendly_login_error_not_debugger(self):
        with patch("routes.auth.execute_query", side_effect=RuntimeError("database offline")):
            response = self.client.post(
                "/officer/login",
                data={"username": "unknown", "password": "invalid"},
            )

        assert response.status_code == 503
        assert b"Sign-in service is unavailable" in response.data
        assert b"Werkzeug Debugger" not in response.data

    def test_officer_audit_log_shows_review_records(self):
        with self.client.session_transaction() as session:
            session["user_id"] = 0
            session["username"] = "officer1"
            session["role"] = "officer"
            session["demo_mode"] = True

        response = self.client.get("/officer/audit-logs")

        assert response.status_code == 200
        for value in (
            b"REV00125",
            b"TX00125",
            b"OFF102",
            b"HOLD",
            b"Requires additional verification",
            b"10:42 AM",
            b"APPROVE",
            b"REJECT",
        ):
            assert value in response.data

    def test_officer_audit_log_loads_review_actions_from_database(self):
        with self.client.session_transaction() as session:
            session["user_id"] = 6
            session["username"] = "officer1"
            session["role"] = "officer"

        rows = [{
            "review_id": 125,
            "transaction_id": 125,
            "officer_id": 102,
            "decision": "HOLD",
            "remarks": "Requires additional verification",
            "reviewed_at": None,
        }]
        with patch("routes.officer.execute_query", return_value=rows) as query:
            response = self.client.get("/officer/audit-logs")

        assert response.status_code == 200
        assert b"REV00125" in response.data
        assert "FROM   manual_reviews" in query.call_args.args[0]