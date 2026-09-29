-- ─────────────────────────────────────────────────────────────────────────────
-- database/seed.sql
-- Synthetic demo data – NO real customer information.
-- All accounts, names, and transactions are fictional.
-- Run AFTER schema.sql.
-- ─────────────────────────────────────────────────────────────────────────────

USE bank_screening;

-- ── Users (passwords are Werkzeug pbkdf2:sha256 hashes) ──────────────────────
-- customer1  → password: demo1234
-- customer2  → password: demo1234
-- customer3  → password: demo1234
-- customer4  → password: demo1234
-- customer5  → password: demo1234
-- officer1   → password: officer123
-- officer2   → password: officer123

INSERT INTO users (username, password_hash, role) VALUES
('arjun.mehta@demo.bank',
 'pbkdf2:sha256:260000$xK3mNpQwR8vT2uYj$a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2',
 'customer'),
('priya.sharma@demo.bank',
 'pbkdf2:sha256:260000$xK3mNpQwR8vT2uYj$a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2',
 'customer'),
('ravi.kumar@demo.bank',
 'pbkdf2:sha256:260000$xK3mNpQwR8vT2uYj$a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2',
 'customer'),
('sunita.patel@demo.bank',
 'pbkdf2:sha256:260000$xK3mNpQwR8vT2uYj$a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2',
 'customer'),
('amit.verma@demo.bank',
 'pbkdf2:sha256:260000$xK3mNpQwR8vT2uYj$a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2',
 'customer'),
('officer1',
 'pbkdf2:sha256:260000$xK3mNpQwR8vT2uYj$a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2',
 'officer'),
('officer2',
 'pbkdf2:sha256:260000$xK3mNpQwR8vT2uYj$a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2',
 'officer');

-- ── Customers ─────────────────────────────────────────────────────────────────
INSERT INTO customers (name, email, phone, status) VALUES
('Arjun Mehta',  'arjun.mehta@demo.bank',  '+91-98001-11001', 'active'),
('Priya Sharma', 'priya.sharma@demo.bank', '+91-98001-11002', 'active'),
('Ravi Kumar',   'ravi.kumar@demo.bank',   '+91-98001-11003', 'active'),
('Sunita Patel', 'sunita.patel@demo.bank', '+91-98001-11004', 'active'),
('Amit Verma',   'amit.verma@demo.bank',   '+91-98001-11005', 'active');

-- ── Accounts ──────────────────────────────────────────────────────────────────
INSERT INTO accounts (customer_id, account_number, balance, status) VALUES
(1, 'ACC1001', 125000.00, 'active'),
(2, 'ACC1002',  48000.00, 'active'),
(3, 'ACC1003',  92500.00, 'active'),
(4, 'ACC1004',  15000.00, 'active'),
(5, 'ACC1005', 310000.00, 'active');

-- ── Historical Transactions (normal – used to establish behaviour baseline) ───
INSERT INTO transactions
    (sender_account, receiver_account, amount, transaction_type,
     transaction_time, reference_number, status)
VALUES
-- Arjun's normal history (small, regular transfers)
('ACC1001','ACC1002', 1000.00,'NEFT', NOW() - INTERVAL 30 DAY, 'REF0000000001','APPROVED'),
('ACC1001','ACC1002', 2500.00,'NEFT', NOW() - INTERVAL 25 DAY, 'REF0000000002','APPROVED'),
('ACC1001','ACC1003', 2000.00,'IMPS', NOW() - INTERVAL 20 DAY, 'REF0000000003','APPROVED'),
('ACC1001','ACC1002', 1500.00,'UPI',  NOW() - INTERVAL 15 DAY, 'REF0000000004','APPROVED'),
('ACC1001','ACC1003', 3000.00,'NEFT', NOW() - INTERVAL 10 DAY, 'REF0000000005','APPROVED'),
('ACC1001','ACC1002', 2000.00,'UPI',  NOW() - INTERVAL  7 DAY, 'REF0000000006','APPROVED'),
-- Priya's normal history
('ACC1002','ACC1003', 5000.00,'NEFT', NOW() - INTERVAL 28 DAY, 'REF0000000007','APPROVED'),
('ACC1002','ACC1003', 4500.00,'RTGS', NOW() - INTERVAL 18 DAY, 'REF0000000008','APPROVED'),
('ACC1002','ACC1001', 3000.00,'NEFT', NOW() - INTERVAL  9 DAY, 'REF0000000009','APPROVED'),
-- Ravi's normal history
('ACC1003','ACC1001', 8000.00,'NEFT', NOW() - INTERVAL 22 DAY, 'REF0000000010','APPROVED'),
('ACC1003','ACC1002', 6000.00,'IMPS', NOW() - INTERVAL 12 DAY, 'REF0000000011','APPROVED'),
-- Amit's normal history
('ACC1005','ACC1001', 5000.00,'UPI',  NOW() - INTERVAL 26 DAY, 'REF0000000012','APPROVED'),
('ACC1005','ACC1002', 7500.00,'NEFT', NOW() - INTERVAL 16 DAY, 'REF0000000013','APPROVED'),
('ACC1005','ACC1003', 6000.00,'IMPS', NOW() - INTERVAL  6 DAY, 'REF0000000014','APPROVED');

-- ── Screening results for normal transactions (LOW risk) ──────────────────────
INSERT INTO screening_results (transaction_id, risk_score, risk_level, triggered_signals, screened_at)
SELECT transaction_id, 10, 'LOW', '[]', transaction_time
FROM transactions WHERE transaction_id BETWEEN 1 AND 14;

-- ── Potentially Suspicious Transactions ───────────────────────────────────────
-- TX 15: Arjun sends unusually large amount (80,000) to a new account (ACC9999)
INSERT INTO transactions
    (sender_account, receiver_account, amount, transaction_type,
     transaction_time, reference_number, status)
VALUES
('ACC1001','ACC9999', 80000.00,'RTGS', NOW() - INTERVAL 2 DAY,
 'REF0000000015','UNDER_REVIEW');

-- TX 16: Rapid fire – 6 transfers in 30 minutes (frequency breach)
INSERT INTO transactions
    (sender_account, receiver_account, amount, transaction_type,
     transaction_time, reference_number, status)
VALUES
('ACC1005','ACC1001', 4000.00,'UPI', NOW() - INTERVAL 1 DAY - INTERVAL 30 MINUTE,'REF0000000016','UNDER_REVIEW'),
('ACC1005','ACC1002', 4500.00,'UPI', NOW() - INTERVAL 1 DAY - INTERVAL 25 MINUTE,'REF0000000017','UNDER_REVIEW'),
('ACC1005','ACC1003', 3800.00,'UPI', NOW() - INTERVAL 1 DAY - INTERVAL 20 MINUTE,'REF0000000018','UNDER_REVIEW'),
('ACC1005','ACC1004', 4200.00,'UPI', NOW() - INTERVAL 1 DAY - INTERVAL 15 MINUTE,'REF0000000019','UNDER_REVIEW'),
('ACC1005','ACC1001', 3600.00,'UPI', NOW() - INTERVAL 1 DAY - INTERVAL 10 MINUTE,'REF0000000020','UNDER_REVIEW'),
('ACC1005','ACC1002', 4100.00,'IMPS',NOW() - INTERVAL 1 DAY - INTERVAL  5 MINUTE,'REF0000000021','UNDER_REVIEW');

-- TX 22: Sunita sends a large amount to a completely new account
INSERT INTO transactions
    (sender_account, receiver_account, amount, transaction_type,
     transaction_time, reference_number, status)
VALUES
('ACC1004','ACC9888', 12000.00,'NEFT', NOW() - INTERVAL 3 HOUR,
 'REF0000000022','UNDER_REVIEW');

-- ── Screening results for suspicious transactions (MEDIUM / HIGH risk) ─────────
INSERT INTO screening_results (transaction_id, risk_score, risk_level, triggered_signals, screened_at) VALUES
(15, 65, 'HIGH',
 '["Unusual amount – Amount ₹80,000.00 is 32.0× your typical average of ₹2,000.00 (threshold: 3.0×)",
   "New recipient – First-ever transfer to account ACC9999",
   "Unusual pattern – Transaction is 8.2 standard deviations above your historical mean (threshold: 2.0σ)"]',
 NOW() - INTERVAL 2 DAY),
(16, 35, 'MEDIUM', '["High transaction frequency – 6 transactions in the last 60 min (limit: 5)"]', NOW() - INTERVAL 1 DAY),
(17, 35, 'MEDIUM', '["High transaction frequency – 6 transactions in the last 60 min (limit: 5)"]', NOW() - INTERVAL 1 DAY),
(18, 35, 'MEDIUM', '["High transaction frequency – 6 transactions in the last 60 min (limit: 5)"]', NOW() - INTERVAL 1 DAY),
(19, 35, 'MEDIUM', '["High transaction frequency – 6 transactions in the last 60 min (limit: 5)"]', NOW() - INTERVAL 1 DAY),
(20, 35, 'MEDIUM', '["High transaction frequency – 6 transactions in the last 60 min (limit: 5)"]', NOW() - INTERVAL 1 DAY),
(21, 35, 'MEDIUM', '["High transaction frequency – 6 transactions in the last 60 min (limit: 5)"]', NOW() - INTERVAL 1 DAY),
(22, 45, 'MEDIUM',
 '["New recipient – First-ever transfer to account ACC9888",
   "Unusual amount – Amount ₹12,000.00 is 5.3× your typical average of ₹2,263.00 (threshold: 3.0×)"]',
 NOW() - INTERVAL 3 HOUR);

-- ── Audit log seed entries ────────────────────────────────────────────────────
INSERT INTO audit_logs (user_id, action, transaction_id, remarks, timestamp) VALUES
(1, 'LOGIN',                NULL, 'User arjun.mehta@demo.bank logged in',            NOW() - INTERVAL 30 DAY),
(1, 'TRANSACTION_CREATED',     1, 'Transfer ₹1,000.00 → ACC1002',                    NOW() - INTERVAL 30 DAY),
(1, 'SCREENING_COMPLETE',      1, 'Risk=LOW Score=10',                                NOW() - INTERVAL 30 DAY),
(1, 'TRANSACTION_STATUS_UPDATED', 1, 'Status → APPROVED',                            NOW() - INTERVAL 30 DAY),
(6, 'LOGIN',                NULL, 'User officer1 logged in',                          NOW() - INTERVAL  2 DAY),
(6, 'OFFICER_APPROVE',        14, 'Routine approval after manual check',              NOW() - INTERVAL  2 DAY);
