import time
import threading
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# =========================
# 🔴 CONFIG
# =========================
TARGET_PROFIT = float(os.getenv("TARGET_PROFIT", 1000))
STOP_LOSS = float(os.getenv("STOP_LOSS", -1000))
MAX_TRADE_TIME = int(os.getenv("MAX_TRADE_TIME", 1800))

SL_DELAY = 7
TARGET_DELAY = 10
CHECK_INTERVAL = 3

# 🔥 NEW FEATURES
BREAKEVEN_TRIGGER = float(os.getenv("BREAKEVEN_TRIGGER", 400))
TRAIL_DISTANCE = float(os.getenv("TRAIL_DISTANCE", 300))
PARTIAL_BOOK = float(os.getenv("PARTIAL_BOOK", 500))

# =========================
# 🔴 STATE
# =========================
active_trade = None


# =========================
# 🔴 START TRACKING
# =========================
def start_trade(kite, symbol, qty, entry_price, side, send_telegram):
    global active_trade

    active_trade = {
        "symbol": symbol,
        "qty": qty,
        "entry_price": entry_price,
        "side": side,
        "start_time": time.time(),

        # 🔥 NEW STATE
        "breakeven_done": False,
        "partial_done": False,
        "highest_pnl": 0
    }

    threading.Thread(
        target=monitor_trade,
        args=(kite, send_telegram),
        daemon=True
    ).start()


# =========================
# 🔴 REAL PNL
# =========================
def get_real_pnl(kite, symbol):
    try:
        positions = kite.positions()["net"]

        for p in positions:
            if p["tradingsymbol"] == symbol and p["quantity"] != 0:
                return p["pnl"]

        return 0

    except Exception as e:
        logging.error(f"PnL error: {str(e)}")
        return 0


# =========================
# 🔴 POSITION CHECK
# =========================
def is_position_open(kite, symbol):
    try:
        positions = kite.positions()["net"]

        for p in positions:
            if p["tradingsymbol"] == symbol and p["quantity"] != 0:
                return True

        return False

    except Exception as e:
        logging.error(f"Position check error: {str(e)}")
        return False


# =========================
# 🔴 MONITOR TRADE
# =========================
def monitor_trade(kite, send_telegram):
    global active_trade

    while active_trade:
        try:
            symbol = active_trade["symbol"]
            qty = active_trade["qty"]

            # 🔴 Ensure position exists
            if not is_position_open(kite, symbol):
                logging.warning("No open position. Stop tracking.")
                active_trade = None
                return

            pnl = get_real_pnl(kite, symbol)
            logging.info(f"{symbol} | PnL: {pnl}")

            # =========================
            # 🔥 TRACK HIGHEST PNL
            # =========================
            if pnl > active_trade["highest_pnl"]:
                active_trade["highest_pnl"] = pnl

            # =========================
            # 🔥 PARTIAL EXIT (50%)
            # =========================
            if (
                pnl >= PARTIAL_BOOK
                and not active_trade["partial_done"]
            ):
                exit_qty = max(1, qty // 2)

                kite.place_order(
                    variety=kite.VARIETY_REGULAR,
                    exchange=kite.EXCHANGE_NFO,
                    tradingsymbol=symbol,
                    transaction_type=kite.TRANSACTION_TYPE_SELL,
                    quantity=exit_qty,
                    product=kite.PRODUCT_MIS,
                    order_type=kite.ORDER_TYPE_MARKET
                )

                active_trade["qty"] -= exit_qty
                active_trade["partial_done"] = True

                send_telegram(f"💰 Partial Exit: {exit_qty}")
                logging.info("Partial exit done")

            # =========================
            # 🔥 BREAK-EVEN
            # =========================
            if (
                pnl >= BREAKEVEN_TRIGGER
                and not active_trade["breakeven_done"]
            ):
                time.sleep(3)

                pnl_check = get_real_pnl(kite, symbol)

                if pnl_check >= BREAKEVEN_TRIGGER:
                    active_trade["breakeven_done"] = True
                    send_telegram("🔒 Break-even activated")
                    logging.info("Break-even activated")

            # =========================
            # 🔥 TRAILING SL
            # =========================
            trail_sl = active_trade["highest_pnl"] - TRAIL_DISTANCE

            if pnl <= trail_sl and active_trade["highest_pnl"] > BREAKEVEN_TRIGGER:
                send_telegram(f"🔻 Trailing SL Hit: {pnl}")
                exit_trade(kite, send_telegram)
                break

            # =========================
            # 🔴 STOP LOSS
            # =========================
            if pnl <= STOP_LOSS:
                time.sleep(SL_DELAY)

                pnl_check = get_real_pnl(kite, symbol)

                if pnl_check <= STOP_LOSS:
                    send_telegram(f"🛑 SL HIT: {pnl_check}")
                    exit_trade(kite, send_telegram)
                    break

            # =========================
            # 🔴 TARGET
            # =========================
            if pnl >= TARGET_PROFIT:
                time.sleep(TARGET_DELAY)

                pnl_check = get_real_pnl(kite, symbol)

                if pnl_check >= TARGET_PROFIT:
                    send_telegram(f"🎯 TARGET HIT: {pnl_check}")
                    exit_trade(kite, send_telegram)
                    break

            # =========================
            # 🔴 TIME EXIT
            # =========================
            if time.time() - active_trade["start_time"] > MAX_TRADE_TIME:
                send_telegram("⏱ Time exit")
                exit_trade(kite, send_telegram)
                break

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            logging.error(f"Monitor error: {str(e)}")


# =========================
# 🔴 EXIT TRADE
# =========================
def exit_trade(kite, send_telegram):
    global active_trade

    try:
        if not active_trade:
            return

        symbol = active_trade["symbol"]
        qty = active_trade["qty"]

        if not is_position_open(kite, symbol):
            send_telegram("⚠️ No open position")
            active_trade = None
            return

        kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NFO,
            tradingsymbol=symbol,
            transaction_type=kite.TRANSACTION_TYPE_SELL,
            quantity=qty,
            product=kite.PRODUCT_MIS,
            order_type=kite.ORDER_TYPE_MARKET
        )

        send_telegram(f"❌ Exit: {symbol}")

    except Exception as e:
        logging.error(str(e))
        send_telegram(f"❌ Exit error: {str(e)}")

    finally:
        active_trade = None