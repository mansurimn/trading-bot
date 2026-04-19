# 📌 Trading Automation Bot

---

## 🧠 System Overview

This is a **production-grade semi-automated trading system** that connects TradingView signals with Zerodha Kite API, enhanced with a robust execution engine, risk management, and adaptive strategy logic.

TradingView → Webhook → Flask Bot → Strategy Engine → Kite API → Execution → Risk Engine → Exit

---

## ⚡ Key Capabilities

✔ Automated trade execution from TradingView  
✔ Volatility-based strategy switching (Directional / Straddle)  
✔ Smart capital allocation (lot sizing based on premium & margin)  
✔ Real-time PnL tracking from Kite  
✔ Advanced risk engine (SL, Target, Trailing SL, Partial exit)  
✔ Time-based trading filter (avoids early market noise)  
✔ Order execution confirmation (no duplicate trades)  
✔ Retry-safe API calls  
✔ Full logging system  

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

### bot.py
Handles webhook, strategy selection, execution, and risk trigger.

### Strategy Engine
Directional (CE/PE) and Straddle based on volatility.

### Volatility Switching
AUTO_MODE=true  
VOL_THRESHOLD=20  

### Risk Manager
SL, Target, Trailing SL, Partial Exit, Time Exit

### Straddle Manager
Dual-leg trade + trailing SL + exit logic

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

python kite_login.py  
python bot.py  
ngrok http 5000  

---

## ⚠️ Notes

- Token expires daily  
- Start in DRY_RUN  
- Test before live  

---

## 💡 Final Thought

Execution + Risk + Discipline
