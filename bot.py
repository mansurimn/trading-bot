from flask import Flask, request
import requests, threading, time, logging, os
from datetime import datetime
from dotenv import load_dotenv
from kiteconnect import KiteConnect

from instrument_manager import get_atm_option
from risk_manager import start_trade, active_trade
from straddle_manager import start_straddle, active_straddle

load_dotenv()

app = Flask(__name__)

kite = KiteConnect(api_key=os.getenv("KITE_API_KEY"))
kite.set_access_token(os.getenv("KITE_ACCESS_TOKEN"))

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

CAPITAL_PER_TRADE = float(os.getenv("CAPITAL_PER_TRADE", 10000))
ENTRY_DELAY = int(os.getenv("ENTRY_DELAY", 15))
STRATEGY_MODE = int(os.getenv("STRATEGY_MODE", 1))

MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", 3000))
MAX_DAILY_PROFIT = float(os.getenv("MAX_DAILY_PROFIT", 3000))

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

# 🔥 NEW CONFIG
AUTO_MODE = os.getenv("AUTO_MODE", "false").lower() == "true"
VOL_THRESHOLD = float(os.getenv("VOL_THRESHOLD", 20))

blocked = False
current_day = datetime.now().date()

# =========================
# 🔴 LOGGER
# =========================
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename=f"logs/bot_{current_day}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log(msg):
    print(msg)
    logging.info(msg)

# =========================
# 🔴 TELEGRAM
# =========================
def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )
    except Exception as e:
        logging.error(f"Telegram error: {str(e)}")

# =========================
# 🔴 RETRY WRAPPER
# =========================
def retry_api(func, retries=3, delay=1):
    for i in range(retries):
        try:
            return func()
        except Exception as e:
            logging.error(f"Retry {i+1} failed: {str(e)}")
            time.sleep(delay)
    return None

# =========================
# 🔴 VOLATILITY FUNCTION (NEW)
# =========================
def get_volatility():
    try:
        p1 = retry_api(lambda: kite.ltp("NSE:NIFTY 50"))
        time.sleep(4)
        p2 = retry_api(lambda: kite.ltp("NSE:NIFTY 50"))

        if not p1 or not p2:
            return 0

        price1 = p1["NSE:NIFTY 50"]["last_price"]
        price2 = p2["NSE:NIFTY 50"]["last_price"]

        vol = abs(price2 - price1)

        log(f"Volatility: {vol}")

        return vol

    except Exception as e:
        logging.error(f"Vol error: {str(e)}")
        return 0

# =========================
# 🔴 ORDER STATUS
# =========================
def get_order_status(order_id):
    try:
        orders = retry_api(lambda: kite.orders())
        if not orders:
            return None

        for o in orders:
            if o["order_id"] == order_id:
                return o["status"]

        return None
    except Exception as e:
        logging.error(f"Order status error: {str(e)}")
        return None

def wait_for_execution(order_id, timeout=10):
    start = time.time()

    while time.time() - start < timeout:
        status = get_order_status(order_id)

        if status == "COMPLETE":
            return True

        if status in ["REJECTED", "CANCELLED"]:
            return False

        time.sleep(1)

    return False

# =========================
# 🔴 LOT SIZE
# =========================
def get_lot_size(symbol):
    return 65 if "NIFTY" in symbol else 20

# =========================
# 🔴 DAILY RESET
# =========================
def daily_reset():
    global blocked, current_day

    today = datetime.now().date()

    if today != current_day:
        blocked = False
        current_day = today
        log("🔄 Daily reset")
        send_telegram("🔄 Bot reset")

# =========================
# 🔴 PNL
# =========================
def get_daily_pnl():
    try:
        data = retry_api(lambda: kite.positions())
        if not data:
            return 0
        return sum(p["pnl"] for p in data["net"])
    except:
        return 0

# =========================
# 🔴 MARGIN CHECK
# =========================
def check_margin(symbol, qty):
    try:
        margins = retry_api(lambda: kite.margins())
        ltp_data = retry_api(lambda: kite.ltp(f"NFO:{symbol}"))

        if not margins or not ltp_data:
            return False

        available = margins["equity"]["available"]["cash"]
        ltp = ltp_data[f"NFO:{symbol}"]["last_price"]

        required = ltp * qty * 1.2

        if available < required:
            send_telegram("❌ Margin low")
            return False

        return True

    except Exception as e:
        logging.error(str(e))
        return False

# =========================
# 🔴 QUANTITY
# =========================
def calculate_quantity(symbol):
    try:
        ltp_data = retry_api(lambda: kite.ltp(f"NFO:{symbol}"))
        margins = retry_api(lambda: kite.margins())

        if not ltp_data or not margins:
            return get_lot_size(symbol)

        ltp = ltp_data[f"NFO:{symbol}"]["last_price"]
        lot = get_lot_size(symbol)

        if ltp <= 0:
            return lot

        capital = min(
            CAPITAL_PER_TRADE,
            margins["equity"]["available"]["cash"] * 0.8
        )

        lots = int(capital / (ltp * lot))
        return max(1, lots) * lot

    except Exception as e:
        logging.error(str(e))
        return get_lot_size(symbol)

# =========================
# 🔴 time 
# =========================
def is_trading_allowed():
    now = datetime.now().time()

    open_start = datetime.strptime(os.getenv("OPEN_START", "09:40"), "%H:%M").time()
    open_end = datetime.strptime(os.getenv("OPEN_END", "10:30"), "%H:%M").time()

    mid_start = datetime.strptime(os.getenv("MID_START", "10:30"), "%H:%M").time()
    mid_end = datetime.strptime(os.getenv("MID_END", "13:30"), "%H:%M").time()

    close_start = datetime.strptime(os.getenv("CLOSE_START", "13:30"), "%H:%M").time()
    close_end = datetime.strptime(os.getenv("CLOSE_END", "15:30"), "%H:%M").time()

    allowed = (
        (open_start <= now <= open_end) or
        (mid_start <= now <= mid_end) or
        (close_start <= now <= close_end)
    )

    logging.info(f"Time Check → Now: {now} | Allowed: {allowed}")

    return allowed

# =========================
# 🔴 PLACE ORDER
# =========================
def place(symbol):
    try:
        qty = calculate_quantity(symbol)

        if not check_margin(symbol, qty):
            return

        if DRY_RUN:
            send_telegram(f"🧪 {symbol} | Qty {qty}")
            return

        order_id = retry_api(lambda: kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NFO,
            tradingsymbol=symbol,
            transaction_type=kite.TRANSACTION_TYPE_BUY,
            quantity=qty,
            product=kite.PRODUCT_MIS,
            order_type=kite.ORDER_TYPE_MARKET
        ))

        if not order_id:
            send_telegram("❌ Order failed")
            return

        log(f"Order placed ID: {order_id}")

        if not wait_for_execution(order_id):
            send_telegram("❌ Order not confirmed")
            return

        send_telegram(f"✅ Order executed: {symbol}")

        ltp_data = retry_api(lambda: kite.ltp(f"NFO:{symbol}"))
        if not ltp_data:
            return

        ltp = ltp_data[f"NFO:{symbol}"]["last_price"]

        start_trade(kite, symbol, qty, ltp, "BUY", send_telegram)

    except Exception as e:
        logging.error(str(e))
        send_telegram("❌ Order error")

# =========================
# 🔴 WEBHOOK
# =========================
@app.route('/webhook', methods=['POST'])
def webhook():
    global blocked

    daily_reset()

    signal = request.data.decode().strip()

    if signal not in ["BUY_CE", "BUY_PE"]:
        return "invalid"

    if not is_trading_allowed():
        log("⛔ Trade blocked (outside trading window)")
        return "time_blocked"
    
    pnl = get_daily_pnl()

    if pnl <= -MAX_DAILY_LOSS:
        blocked = True
        send_telegram("🛑 Max Loss Hit")
        return "blocked"

    if pnl >= MAX_DAILY_PROFIT:
        blocked = True
        send_telegram("💰 Target Hit")
        return "blocked"

    if blocked or active_trade or active_straddle:
        return "blocked"
    
    def run():
        try:
            time.sleep(ENTRY_DELAY)

            # 🔥 VOLATILITY SWITCH
            vol = get_volatility()

            if AUTO_MODE:
                strategy = 2 if vol > VOL_THRESHOLD else 1
                log(f"AUTO MODE → Vol: {vol} | Strategy: {strategy}")
            else:
                strategy = STRATEGY_MODE

            opt = get_atm_option(kite, "NIFTY", "CE" if signal == "BUY_CE" else "PE")

            if not opt:
                send_telegram("❌ Option fetch failed")
                return

            if strategy == 1:
                place(opt)

            elif strategy == 2:
                ce = get_atm_option(kite, "NIFTY", "CE")
                pe = get_atm_option(kite, "NIFTY", "PE")

                if not ce or not pe:
                    send_telegram("❌ Straddle fetch failed")
                    return
                qty = calculate_quantity(ce)
                log(f"Starting straddle | CE: {ce} PE: {pe}")
                start_straddle(kite, ce, pe, qty, send_telegram)

        except Exception as e:
            logging.error(str(e))

    threading.Thread(target=run, daemon=True).start()

    return "ok"

# =========================
# 🔴 START
# =========================
if __name__ == "__main__":
    send_telegram("🚀 Bot Started")
    log("Bot started")
    app.run(port=5000)