"""
tests/test_screening.py
────────────────────────
Unit tests for the fraud screening rules (no DB required – uses mocking).
Run with: python -m pytest tests/ -v
"""

import sys
import os
import json
import unittest
from unittest.mock import patch, MagicMock

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ── Mock the database module before importing screening ───────────────────────
db_mock = MagicMock()
sys.modules['database'] = db_mock

from config import Config


# ──────────────────────────────────────────────────────────────────────────────
# Test 1 – Normal transaction (small, known recipient, low frequency)
# ──────────────────────────────────────────────────────────────────────────────
class TestNormalTransaction(unittest.TestCase):
    def test_low_risk_small_amount(self):
        """A small, within-average amount to a known recipient → LOW risk."""
        from screening.fraud_rules import rule_unusual_amount, rule_new_recipient

        # history: [1000, 2000, 1500, 2500, 1800]  mean≈1760
        with patch('screening.fraud_rules._recent_amounts', return_value=[1000, 2000, 1500, 2500, 1800]):
            triggered, reason = rule_unusual_amount('ACC1001', 2000.0)
        self.assertFalse(triggered, "Amount 2000 should NOT trigger unusual amount rule")

    def test_known_recipient_no_trigger(self):
        """Known recipient (prior transfer exists) → no new-recipient signal."""
        from screening.fraud_rules import rule_new_recipient
        with patch('screening.fraud_rules._has_prior_transfer', return_value=True):
            triggered, reason = rule_new_recipient('ACC1001', 'ACC1002')
        self.assertFalse(triggered)


# ──────────────────────────────────────────────────────────────────────────────
# Test 2 – Unusual Amount
# ──────────────────────────────────────────────────────────────────────────────
class TestUnusualAmount(unittest.TestCase):
    def test_large_amount_triggers_rule(self):
        """Amount 80,000 against a mean of ~2,000 should trigger the rule."""
        from screening.fraud_rules import rule_unusual_amount

        history = [1000.0, 2000.0, 1500.0, 2500.0, 2000.0]  # mean ≈ 1800
        with patch('screening.fraud_rules._recent_amounts', return_value=history):
            triggered, reason = rule_unusual_amount('ACC1001', 80000.0)

        self.assertTrue(triggered, "80,000 should trigger unusual amount rule")
        self.assertIn("₹80,000.00", reason)

    def test_insufficient_history_skips_rule(self):
        """If < UNUSUAL_AMOUNT_MIN_SAMPLES priors, rule should not fire."""
        from screening.fraud_rules import rule_unusual_amount

        with patch('screening.fraud_rules._recent_amounts', return_value=[1000.0, 2000.0]):
            triggered, _ = rule_unusual_amount('ACC1001', 80000.0)

        self.assertFalse(triggered, "Insufficient history should skip rule")


# ──────────────────────────────────────────────────────────────────────────────
# Test 3 – New Recipient
# ──────────────────────────────────────────────────────────────────────────────
class TestNewRecipient(unittest.TestCase):
    def test_new_recipient_triggers(self):
        """First-ever transfer to a new account → triggers rule."""
        from screening.fraud_rules import rule_new_recipient
        with patch('screening.fraud_rules._has_prior_transfer', return_value=False):
            triggered, reason = rule_new_recipient('ACC1001', 'ACC9999')
        self.assertTrue(triggered)
        self.assertIn('ACC9999', reason)

    def test_existing_recipient_no_trigger(self):
        """Known recipient → does not trigger rule."""
        from screening.fraud_rules import rule_new_recipient
        with patch('screening.fraud_rules._has_prior_transfer', return_value=True):
            triggered, _ = rule_new_recipient('ACC1001', 'ACC1002')
        self.assertFalse(triggered)


# ──────────────────────────────────────────────────────────────────────────────
# Test 4 – High Frequency
# ──────────────────────────────────────────────────────────────────────────────
class TestHighFrequency(unittest.TestCase):
    def test_high_frequency_triggers(self):
        """6 transactions in 60 min (limit=5) → triggers rule."""
        from screening.fraud_rules import rule_high_frequency
        with patch('screening.fraud_rules._recent_tx_count_in_window', return_value=6):
            triggered, reason = rule_high_frequency('ACC1005')
        self.assertTrue(triggered)
        self.assertIn('6', reason)

    def test_normal_frequency_no_trigger(self):
        """3 transactions in 60 min (limit=5) → no trigger."""
        from screening.fraud_rules import rule_high_frequency
        with patch('screening.fraud_rules._recent_tx_count_in_window', return_value=3):
            triggered, _ = rule_high_frequency('ACC1005')
        self.assertFalse(triggered)


# ──────────────────────────────────────────────────────────────────────────────
# Test 5 – Unusual Pattern (Z-score)
# ──────────────────────────────────────────────────────────────────────────────
class TestUnusualPattern(unittest.TestCase):
    def test_high_z_score_triggers(self):
        """Amount far above mean + low stdev → high Z-score → triggers."""
        from screening.fraud_rules import rule_unusual_pattern
        # mean=2000, stdev≈100 → 80000 is way above
        with patch('screening.fraud_rules._recent_amounts',
                   return_value=[1900.0, 2000.0, 2100.0, 2050.0, 1950.0]):
            triggered, reason = rule_unusual_pattern('ACC1001', 80000.0)
        self.assertTrue(triggered)

    def test_normal_pattern_no_trigger(self):
        """Amount within 1 stdev of mean → no trigger."""
        from screening.fraud_rules import rule_unusual_pattern
        with patch('screening.fraud_rules._recent_amounts',
                   return_value=[1800.0, 2000.0, 2200.0, 1900.0, 2100.0]):
            triggered, _ = rule_unusual_pattern('ACC1001', 2100.0)
        self.assertFalse(triggered)


# ──────────────────────────────────────────────────────────────────────────────
# Test 6 – Risk Score accumulation
# ──────────────────────────────────────────────────────────────────────────────
class TestRiskScoring(unittest.TestCase):
    def test_high_risk_score_routes_to_review(self):
        """When multiple rules trigger, score should reach HIGH."""
        with patch('screening.risk_engine.screen_transaction') as mock_screen:
            mock_screen.return_value = {
                'risk_score': 65,
                'risk_level': 'HIGH',
                'triggered_signals': ['Unusual amount', 'New recipient', 'Unusual pattern'],
                'should_review': True,
            }
            result = mock_screen(1, 'ACC1001', 'ACC9999', 80000.0)

        self.assertEqual(result['risk_level'], 'HIGH')
        self.assertTrue(result['should_review'])
        self.assertGreaterEqual(result['risk_score'], 60)

    def test_low_risk_no_review(self):
        """When no rules trigger, score stays LOW."""
        with patch('screening.risk_engine.screen_transaction') as mock_screen:
            mock_screen.return_value = {
                'risk_score': 10,
                'risk_level': 'LOW',
                'triggered_signals': [],
                'should_review': False,
            }
            result = mock_screen(2, 'ACC1001', 'ACC1002', 2000.0)

        self.assertFalse(result['should_review'])
        self.assertEqual(result['risk_level'], 'LOW')


# ──────────────────────────────────────────────────────────────────────────────
# Test 7 – Risk level thresholds (config-driven)
# ──────────────────────────────────────────────────────────────────────────────
class TestRiskLevelThresholds(unittest.TestCase):
    def test_score_29_is_low(self):
        self.assertLessEqual(29, Config.RISK_LOW_MAX)

    def test_score_30_is_medium(self):
        self.assertGreater(30, Config.RISK_LOW_MAX)
        self.assertLessEqual(30, Config.RISK_MEDIUM_MAX)

    def test_score_60_is_high(self):
        self.assertGreater(60, Config.RISK_MEDIUM_MAX)

    def test_auto_review_triggered_at_medium(self):
        """Auto-review threshold must be <= RISK_MEDIUM_MAX lower bound."""
        self.assertLessEqual(Config.AUTO_REVIEW_THRESHOLD, Config.RISK_MEDIUM_MAX + 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
