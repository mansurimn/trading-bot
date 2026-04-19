# 🚀 Trading Automation Bot

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Flask](https://img.shields.io/badge/Flask-API-green)
![Trading](https://img.shields.io/badge/Trading-Automation-orange)
![Status](https://img.shields.io/badge/Status-Production--Ready-brightgreen)

---

## 🧠 System Overview

Production-grade semi-automated trading system integrating TradingView signals with Zerodha Kite API.

TradingView → Webhook → Flask Bot → Strategy Engine → Kite API → Execution → Risk Engine → Exit


---

## ⚡ Key Capabilities

✔ Automated trade execution from TradingView  
✔ Volatility-based strategy switching  
✔ Smart capital allocation  
✔ Real-time PnL tracking  
✔ Advanced risk engine  
✔ Time-based trading filter  
✔ Order execution confirmation  
✔ Retry-safe API calls  
✔ Full logging system  

---

## 📊 TradingView Integration & Flow

### 🔗 Signal Flow

1. TradingView alert triggers webhook  
2. Bot receives signal  
3. Telegram notification sent  
4. Kite API executes trade  

---

## 🔄 Complete Execution Flow

TradingView Signal →
Bot receives →
Check volatility →
Select instrument →
Select strategy →
Apply entry delay →
Execute order →
Start risk engine →
Monitor PnL →
Exit (SL / Target / Time)


---

## 🧠 Strategy Engine

### 🎯 Strategies

✔ Directional (CE / PE)  
✔ Straddle (volatility play)  
✔ Premium-based instrument switching  
✔ Expiry-based auto selection  

---

## 🛑 Risk Management

✔ Stop Loss  
✔ Target exit  
✔ Break-even shift  
✔ Trailing SL  
✔ Partial profit booking  
✔ Daily max loss lock  
✔ Daily profit lock  
✔ Margin validation  
✔ Single active trade rule  

---

## ⚙️ Entry Filters

✔ Entry delay (fake breakout filter)  
✔ Direction validation  
✔ Premium-based filtering  

---

## 🧩 Project Structure

trading_bot/
│
├── bot.py
├── instrument_manager.py
├── risk_manager.py
├── straddle_manager.py
├── kite_login.py
├── .env
├── logs/


---

## ⚙️ Core Components

### 🟢 bot.py
Handles execution, strategy selection, and webhook processing

### 🟢 Strategy Engine
Switches between directional and straddle

### 🟢 Risk Manager
SL, Target, Trailing, Partial Exit

### 🟢 Straddle Manager
Dual-leg execution + trailing SL

---

## 🧱 Architecture Diagram

<img width="1024" height="1536" alt="image" src="https://github.com/user-attachments/assets/4b4c6475-fb54-483c-9d1c-720563631234" />



---

## 🔐 Configuration (.env)
KITE_API_KEY=xxx
KITE_API_SECRET=xxx
KITE_ACCESS_TOKEN=xxx

TOKEN=xxx
CHAT_ID=xxx

CAPITAL_PER_TRADE=10000
ENTRY_DELAY=15
STRATEGY_MODE=1

MAX_DAILY_LOSS=3000
MAX_DAILY_PROFIT=3000

AUTO_MODE=true
VOL_THRESHOLD=20

OPEN_START=09:40
OPEN_END=10:30
MID_START=10:30
MID_END=13:30
CLOSE_START=13:30
CLOSE_END=15:30

DRY_RUN=true


---

## ▶️ Run

``bash
python kite_login.py
python bot.py
ngrok http 5000

📊 Logging

Logs stored in:

logs/bot_<date>.log

Notes
Access token expires daily
Start with DRY_RUN
Test before live trading

💡 Final Thought
Execution + Risk Management + Discipline = Consistency

---
