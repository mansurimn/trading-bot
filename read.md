# 📌 Trading Automation Bot

## 🧠 System Overview

This project is a **semi-automated trading system** that connects TradingView signals with Zerodha Kite API for execution, enhanced with a custom risk management engine.

```
TradingView → Webhook → Flask Bot → Kite API → Order Execution → Risk Engine → Exit
```

---

## 🧩 Project Structure

```
trading_bot/
│
├── bot.py               # Main trading engine
├── option_utils.py      # Option strike + expiry logic
├── risk_manager.py      # SL / Target / exit system
├── kite_login.py        # Daily authentication
├── .env                 # Config (API keys, tokens)
├── start_trading.bat    # Start bot + ngrok
├── login_kite.bat       # Generate access token
├── logs/                # Daily logs
```

---

## ⚙️ Component Explanation

### 🟢 bot.py (Core Engine)

**Responsibilities:**

* Receive TradingView signals
* Apply trading rules
* Generate option symbols
* Execute trades
* Start risk tracking

**Key Logic:**

1. **Webhook Entry**

```python
@app.route('/webhook', methods=['POST'])
```

Receives signals like:

```
BUY_CE / BUY_PE
```

2. **Risk Filters**

* Duplicate protection
* Counter trade blocking
* Max trades per day
* Single active trade

3. **Price Fetch**

```python
kite.ltp("NSE:NIFTY 50")
```

4. **Symbol Generation**

```python
build_option_symbol(price, "CE")
```

5. **Order Execution**

```python
place_order(symbol, BUY)
```

6. **Risk Engine Trigger**

```python
start_trade(...)
```

---

### 🟢 option_utils.py

Handles conversion of price to tradable option symbols.

**Functions:**

* **ATM Strike**

```python
round(price / 50) * 50
```

* **Weekly Expiry**

* Automatically calculates next Thursday

* **Symbol Format**

```
NIFTY + EXPIRY + STRIKE + CE/PE
```

---

### 🟢 risk_manager.py (Most Important)

**Purpose:** Capital protection

**Features:**

* ✅ Stop Loss
* ✅ Target Profit
* ✅ Time-based Exit (30 mins)
* ✅ Auto Exit using Kite API
* ✅ Monitoring Thread (runs every 5 seconds)

---

### 🟢 kite_login.py

Handles **daily authentication** with Kite.

**Flow:**

1. Generate login URL
2. Login manually
3. Extract `request_token`
4. Generate `access_token`
5. Save to `.env`

⚠️ Access token expires daily

---

### 🟢 .env

Stores all sensitive configuration:

```
TOKEN=telegram_token
CHAT_ID=telegram_chat_id
MAX_TRADES=2

KITE_API_KEY=xxx
KITE_API_SECRET=xxx
KITE_ACCESS_TOKEN=xxx
```

---

### 🟢 BAT Files

#### login_kite.bat

Runs:

```
kite_login.py
```

Used for daily authentication

#### start_trading.bat

* Starts bot
* Starts ngrok

---

## 🔗 Full Workflow

### 🌅 Daily Startup

```
1. Run login_kite.bat
2. Login → token saved
3. Run start_trading.bat
4. Copy ngrok URL
5. Update TradingView webhook
```

---

### 📊 During Market

```
Signal → Bot → Kite → Trade → Risk Engine → Exit
```

---

### 🌙 End of Day

* Logs stored
* System stops

---

## 🧪 Testing Strategy

Before live trading:

* Test DRY_RUN mode
* Validate symbol generation
* Validate SL / Target
* Validate duplicate & counter logic

---

## 🚀 Features

* VWAP-based signal execution
* ATM option auto-selection
* Weekly expiry handling
* Telegram notifications
* Stop Loss / Target / Time exit
* Trade discipline controls

---

## 🧱 Tech Stack

* Python
* Flask
* Kite Connect API
* TradingView Webhooks
* Ngrok

---

## ⚙️ Setup

```bash
pip install flask kiteconnect python-dotenv requests
```

---

## 🔐 Environment Setup

Create `.env` file:

```
TOKEN=xxx
CHAT_ID=xxx
MAX_TRADES=2

KITE_API_KEY=xxx
KITE_API_SECRET=xxx
KITE_ACCESS_TOKEN=xxx
```

---

## ▶️ Run the System

```bash
python kite_login.py
python bot.py
ngrok http 5000
```

---

## ⚠️ Important Notes

* Access token must be generated daily
* Always start in `DRY_RUN` mode
* Test thoroughly before live trading

---

## 🚀 Improvements (Roadmap)

### 🔥 High Priority

1. Real PnL from Kite positions
2. Instrument-based expiry handling
3. Exchange-level Stop Loss orders

---

### 🟡 Medium Priority

4. Dashboard (PnL + trade history)
5. Retry logic for network failures

---

### 🧠 Advanced

6. AI-based trade filtering
7. Multi-strategy engine (VWAP + breakout)

---

## ⚠️ Disclaimer

This project is for educational purposes. Use at your own risk.
Always test thoroughly before deploying with real capital.

---

## 👍 Final Thought

This system is not just about strategy — it's about:

```
Execution + Risk Control + Discipline
```

FINAL SYSTEM (NOW)
Signal →
Check PnL →
    Loss hit → STOP ❌
    Profit hit → STOP 💰
Check Margin →
Execute →
Risk Engine →
Exit