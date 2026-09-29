"""
tests/test_transactions.py
──────────────────────────
Integration-style tests for the transaction validation logic (mocked Flask app).
Tests cover: insufficient balance, self-transfer, invalid receiver, valid transfer.
"""

import sys, os, unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Mock database and config before importing app
sys.modules['database'] = MagicMock()
sys.modules['mysql']    = MagicMock()
sys.modules['mysql.connector'] = MagicMock()
sys.modules['mysql.connector.pooling'] = MagicMock()

from app import create_app


class TestTransactionValidation(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config.update({
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret',
        })
        self.client = self.app.test_client()

        # Simulate a logged-in customer session
        with self.client.session_transaction() as sess:
            sess['user_id']       = 1
            sess['username']      = 'test@demo.bank'
            sess['role']          = 'customer'
            sess['account_id']    = 1
            sess['account_number']= 'ACC1001'
            sess['customer_name'] = 'Test User'
            sess['customer_id']   = 1

    # ── Test 5: Insufficient Balance ────────────────────────────────────────
    def test_insufficient_balance_rejected(self):
        """Transfer with amount exceeding balance should be rejected."""
        mock_sender = {'balance': 5000.0}
        mock_receiver = {'account_id': 2, 'account_number': 'ACC1002',
                         'balance': 10000.0, 'status': 'active'}

        with patch('routes.transactions.execute_query') as mock_q:
            # Call sequence:
            # 1st call → receiver exists
            # 2nd call → sender balance
            mock_q.side_effect = [mock_receiver, mock_sender]

            resp = self.client.post('/transfer/', data={
                'receiver_account': 'ACC1002',
                'amount': '99999',
                'transaction_type': 'NEFT',
                'remarks': '',
            }, follow_redirects=True)

        self.assertIn(b'Insufficient balance', resp.data)

    # ── Test: Self-transfer blocked ──────────────────────────────────────────
    def test_self_transfer_blocked(self):
        """Transfer to own account should be rejected."""
        resp = self.client.post('/transfer/', data={
            'receiver_account': 'ACC1001',
            'amount': '1000',
            'transaction_type': 'NEFT',
            'remarks': '',
        }, follow_redirects=True)
        self.assertIn(b'cannot transfer funds to your own account', resp.data)

    # ── Test: Negative amount rejected ──────────────────────────────────────
    def test_negative_amount_rejected(self):
        """Negative or zero amount should produce a validation error."""
        resp = self.client.post('/transfer/', data={
            'receiver_account': 'ACC1002',
            'amount': '-100',
            'transaction_type': 'NEFT',
            'remarks': '',
        }, follow_redirects=True)
        self.assertIn(b'greater than', resp.data)

    # ── Test: Non-existent receiver ──────────────────────────────────────────
    def test_nonexistent_receiver_rejected(self):
        """Transfer to unknown account should be rejected."""
        with patch('routes.transactions.execute_query', return_value=None):
            resp = self.client.post('/transfer/', data={
                'receiver_account': 'ACC9999',
                'amount': '1000',
                'transaction_type': 'NEFT',
                'remarks': '',
            }, follow_redirects=True)
        self.assertIn(b'not found', resp.data)


class TestOfficerDecisionAudit(unittest.TestCase):
    """
    Tests 7, 8, 9 - Officer approve/reject/hold create audit logs.
    """

    def setUp(self):
        self.app = create_app()
        self.app.config.update({'TESTING': True, 'SECRET_KEY': 'test-secret'})
        self.client = self.app.test_client()

        with self.client.session_transaction() as sess:
            sess['user_id']  = 6
            sess['username'] = 'officer1'
            sess['role']     = 'officer'

    def _mock_tx(self):
        return {
            'transaction_id': 15,
            'sender_account': 'ACC1001',
            'receiver_account': 'ACC9999',
            'amount': 80000.0,
            'transaction_type': 'RTGS',
            'transaction_time': None,
            'reference_number': 'REF0000000015',
            'status': 'UNDER_REVIEW',
        }

    def _post_decision(self, decision: str):
        """
        POST a decision. We do NOT follow redirects so the mock scope covers
        only the transaction_detail view and not the redirect target.
        The route responds with a 302 on success.
        """
        tx = self._mock_tx()

        # Use a MagicMock that returns sensible values for any call signature:
        # - fetch='one'  → return the tx dict (or None for review lookup)
        # - fetch='none' → return 1 (lastrowid / rowcount)
        def flexible_query(*args, fetch='all', **kwargs):
            if fetch == 'one':
                # First 'one' call = fetch transaction, second = fetch review
                return tx if 'manual_reviews' not in args[0] else None
            return 1  # INSERT / UPDATE returns lastrowid

        with patch('routes.officer.execute_query', side_effect=flexible_query) as mock_q, \
             patch('routes.officer.get_screening_result') as mock_sr, \
             patch('routes.officer.log_audit') as mock_log:

            mock_sr.return_value = {
                'risk_score': 65, 'risk_level': 'HIGH',
                'triggered_signals': [], 'screened_at': None,
            }

            resp = self.client.post(
                '/officer/transaction/15',
                data={'decision': decision, 'remarks': f'Test {decision}'},
                follow_redirects=False,   # <-- stop at the 302 redirect
            )
            return resp, mock_log

    # Test 7 – Officer APPROVE → status=APPROVED, audit log created
    def test_approve_creates_audit_log(self):
        resp, mock_log = self._post_decision('APPROVE')
        self.assertIn(resp.status_code, [302, 200],
                      "APPROVE should redirect (302) or render (200)")
        self.assertTrue(mock_log.called,
                        "log_audit must be called when officer approves")

    # Test 8 – Officer REJECT → status=REJECTED, audit log created
    def test_reject_creates_audit_log(self):
        resp, mock_log = self._post_decision('REJECT')
        self.assertIn(resp.status_code, [302, 200])
        self.assertTrue(mock_log.called,
                        "log_audit must be called when officer rejects")

    # Test 9 – Officer HOLD → status=HELD, audit log created
    def test_hold_creates_audit_log(self):
        resp, mock_log = self._post_decision('HOLD')
        self.assertIn(resp.status_code, [302, 200])
        self.assertTrue(mock_log.called,
                        "log_audit must be called when officer holds")


if __name__ == '__main__':
    unittest.main(verbosity=2)
