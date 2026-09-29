-- ─────────────────────────────────────────────────────────────────────────────
-- database/schema.sql
-- Bank Screening System – DDL
-- Run this once to create/reset all tables.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE DATABASE IF NOT EXISTS bank_screening
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE bank_screening;

-- ── users ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id       INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    username      VARCHAR(100)    NOT NULL UNIQUE,
    password_hash VARCHAR(255)    NOT NULL,
    role          ENUM('customer','officer') NOT NULL DEFAULT 'customer',
    is_active     TINYINT(1)      NOT NULL DEFAULT 1,
    created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    INDEX idx_users_username (username)
) ENGINE=InnoDB;

-- ── customers ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customers (
    customer_id   INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    name          VARCHAR(150)    NOT NULL,
    email         VARCHAR(150)    NOT NULL UNIQUE,
    phone         VARCHAR(20),
    status        ENUM('active','inactive','suspended') NOT NULL DEFAULT 'active',
    created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (customer_id),
    INDEX idx_customers_email (email)
) ENGINE=InnoDB;

-- ── accounts ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS accounts (
    account_id     INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    customer_id    INT UNSIGNED    NOT NULL,
    account_number VARCHAR(20)     NOT NULL UNIQUE,
    balance        DECIMAL(15,2)   NOT NULL DEFAULT 0.00,
    status         ENUM('active','inactive','frozen') NOT NULL DEFAULT 'active',
    created_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (account_id),
    INDEX idx_accounts_account_number (account_number),
    CONSTRAINT fk_accounts_customer
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ── transactions ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id   INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    sender_account   VARCHAR(20)   NOT NULL,
    receiver_account VARCHAR(20)   NOT NULL,
    amount           DECIMAL(15,2) NOT NULL,
    transaction_type ENUM('NEFT','RTGS','IMPS','UPI') NOT NULL DEFAULT 'NEFT',
    transaction_time DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reference_number VARCHAR(50)   NOT NULL UNIQUE,
    status           ENUM('PENDING','APPROVED','UNDER_REVIEW','REJECTED','HELD')
                                   NOT NULL DEFAULT 'PENDING',
    PRIMARY KEY (transaction_id),
    INDEX idx_tx_sender   (sender_account),
    INDEX idx_tx_receiver (receiver_account),
    INDEX idx_tx_status   (status),
    INDEX idx_tx_time     (transaction_time)
) ENGINE=InnoDB;

-- ── screening_results ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS screening_results (
    screening_id       INT UNSIGNED NOT NULL AUTO_INCREMENT,
    transaction_id     INT UNSIGNED NOT NULL,
    risk_score         TINYINT      NOT NULL DEFAULT 0,
    risk_level         ENUM('LOW','MEDIUM','HIGH') NOT NULL DEFAULT 'LOW',
    triggered_signals  TEXT,               -- JSON array of reason strings
    screened_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (screening_id),
    INDEX idx_sr_transaction (transaction_id),
    INDEX idx_sr_risk_level  (risk_level),
    CONSTRAINT fk_sr_transaction
        FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ── manual_reviews ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS manual_reviews (
    review_id      INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    transaction_id INT UNSIGNED  NOT NULL,
    officer_id     INT UNSIGNED  NOT NULL,
    decision       ENUM('APPROVE','REJECT','HOLD') NOT NULL,
    remarks        TEXT,
    reviewed_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (review_id),
    INDEX idx_mr_transaction (transaction_id),
    INDEX idx_mr_officer     (officer_id),
    CONSTRAINT fk_mr_transaction
        FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_mr_officer
        FOREIGN KEY (officer_id) REFERENCES users(user_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ── audit_logs ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id         INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    user_id        INT UNSIGNED  NOT NULL,
    action         VARCHAR(100)  NOT NULL,
    transaction_id INT UNSIGNED  DEFAULT NULL,
    remarks        TEXT,
    timestamp      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (log_id),
    INDEX idx_al_user      (user_id),
    INDEX idx_al_action    (action),
    INDEX idx_al_timestamp (timestamp),
    CONSTRAINT fk_al_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;
