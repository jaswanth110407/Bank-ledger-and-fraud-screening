# 🏦 Cooperative Bank Ledger & Fraud Screening System
### B.Tech Student Project — Educational Banking Simulation

> **⚠️ Educational Disclaimer:** This is a synthetic demonstration project using only fictional data. It does **not** connect to real bank accounts, real payment networks, or process real money. All fraud thresholds are project-defined demonstration rules and are **not** official banking or regulatory standards.

---

## 📋 Project Overview

A full-stack web application that simulates a cooperative bank's automated first-level fraud screening system. Every fund transfer is recorded in a digital ledger, automatically screened by a rule-based engine, assigned a transparent risk score, and routed for manual review if suspicious.

### Workflow
```
CUSTOMER → LOGIN → TRANSFER REQUEST → INPUT VALIDATION
    ↓
BANK LEDGER → AUTOMATED SCREENING → RISK SCORE
    ↓                                    ↓
NORMAL (< 30)              SUSPICIOUS (≥ 30)
    ↓                            ↓
AUTO APPROVED           MANUAL REVIEW QUEUE
                              ↓
                       BANK OFFICER
                     APPROVE / REJECT / HOLD
                              ↓
                       UPDATE LEDGER + AUDIT LOG
```

---

## 🛠️ Technology Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| Frontend    | HTML5, Custom CSS3, Vanilla JS       |
| Backend     | Python 3.14, Flask 3.x              |
| Database    | MySQL 8.x                           |
| Security    | Werkzeug pbkdf2:sha256, Flask sessions |
| Dev Tools   | VS Code, Git                        |

---

## 📁 Project Structure

```
BANK-LEDGER-FRAUD-SCREENING/
│
├── app.py               # Flask application factory
├── config.py            # All configuration & thresholds
├── database.py          # MySQL connection pool & query helper
├── setup_db.py          # One-time database initialisation
├── requirements.txt
├── .env.example
│
├── screening/
│   ├── fraud_rules.py   # Individual rule functions
│   └── risk_engine.py   # Orchestrator – score + persist
│
├── routes/
│   ├── auth.py          # Login / logout
│   ├── customer.py      # Customer dashboard, ledger, profile
│   ├── transactions.py  # Fund transfer endpoint
│   ├── officer.py       # Officer dashboard, review, audit
│   └── utils.py         # Decorators, audit logging, pagination
│
├── templates/           # Jinja2 HTML templates
│   ├── base.html
│   ├── login.html
│   ├── customer_dashboard.html
│   ├── officer_dashboard.html
│   ├── ledger.html
│   ├── transfer.html
│   ├── review_queue.html
│   ├── transaction_details.html
│   ├── audit_logs.html
│   ├── transaction_history.html
│   ├── profile.html
│   └── error.html
│
├── static/
│   ├── css/style.css    # Premium dark banking UI
│   └── js/dashboard.js  # Live clock, animations, UX
│
├── database/
│   ├── schema.sql       # DDL – all tables
│   └── seed.sql         # Demo synthetic data
│
└── tests/
    ├── test_screening.py
    └── test_transactions.py
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.10+
- MySQL 8.0+
- pip

### 1. Clone / Open Project

```bash
cd "BANK-LEDGER-FRAUD-SCREENING"
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
copy .env.example .env
# Edit .env with your MySQL credentials
```

`.env` example:
```
SECRET_KEY=your-random-secret-key
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=bank_screening
FLASK_ENV=development
FLASK_DEBUG=1
```

### 4. Set Up Database

```bash
python setup_db.py
```

This will:
- Create the `bank_screening` MySQL database
- Create all tables with proper indexes and foreign keys
- Insert 5 demo customers, 5 accounts, and sample transactions
- Hash all passwords with Werkzeug pbkdf2:sha256

### 5. Run the Application

```bash
python app.py
```

Visit: **http://localhost:5000**

---

## 🔐 Demo Credentials

| Username                    | Password    | Role     |
|-----------------------------|-------------|----------|
| `arjun.mehta@demo.bank`     | `demo1234`  | Customer |
| `priya.sharma@demo.bank`    | `demo1234`  | Customer |
| `ravi.kumar@demo.bank`      | `demo1234`  | Customer |
| `sunita.patel@demo.bank`    | `demo1234`  | Customer |
| `amit.verma@demo.bank`      | `demo1234`  | Customer |
| `officer1`                  | `officer123`| Officer  |
| `officer2`                  | `officer123`| Officer  |

---

## 🔍 Fraud Screening Rules

> All rules and thresholds are project-defined demonstration values.

| Rule | Signal | Points |
|------|--------|--------|
| **Rule 1** | Unusual Amount (> 3× historical average) | +30 |
| **Rule 2** | High Frequency (> 5 transfers in 60 min) | +20 |
| **Rule 3** | New Recipient (first-ever transfer to account) | +15 |
| **Rule 4** | Unusual Pattern (> 2σ above historical mean) | +20 |

### Risk Levels

| Score Range | Level  | Action             |
|-------------|--------|--------------------|
| 0 – 29      | 🟢 LOW   | Auto-approved      |
| 30 – 59     | 🟡 MEDIUM| Manual review queue|
| 60 – 100    | 🔴 HIGH  | Manual review queue|

---

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```

Test coverage:
- Normal transaction → LOW risk
- Unusual amount detection
- New recipient detection
- High frequency detection
- Insufficient balance rejection
- High risk routing to review
- Officer approve / reject / hold + audit log

---

## 🗄️ Database Schema

```
users           → user_id, username, password_hash, role
customers       → customer_id, name, email, phone, status
accounts        → account_id, customer_id, account_number, balance
transactions    → transaction_id, sender, receiver, amount, type, time, ref, status
screening_results → screening_id, transaction_id, risk_score, risk_level, signals
manual_reviews  → review_id, transaction_id, officer_id, decision, remarks
audit_logs      → log_id, user_id, action, transaction_id, remarks, timestamp
```

---

## 🔒 Security Features

- ✅ Werkzeug `pbkdf2:sha256` password hashing
- ✅ Flask server-side sessions (not stored in browser)
- ✅ Role-based access control (`@customer_required`, `@officer_required`)
- ✅ Parameterised SQL queries (no SQL injection)
- ✅ Server-side input validation
- ✅ Environment variable credentials (no hardcoding)
- ✅ Complete audit trail for all actions

---

## 📊 System Roles

### Customer Can:
- Login, view balance, make transfers
- View personal ledger with status and risk level
- View transaction history and profile

### Bank Officer Can:
- View full bank ledger (all accounts)
- See risk scores and screening signals
- Approve / Reject / Hold flagged transactions
- Add review remarks (recorded in audit log)
- View complete audit trail

---

*B.Tech Computer Science Project — Cooperative Bank Ledger & Fraud Screening System*
