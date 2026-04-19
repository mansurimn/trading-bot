import threading
import time
import logging

# =========================
# 🔴 CONFIG
# =========================
PROFIT_THRESHOLD = 500
MAX_LOSS = -1500
CHECK_INTERVAL = 3

TRAIL_GAP = 400   # 🔥 Trailing SL gap
CONFIRM_DELAY = 3 # 🔥 Spike confirmation delay

active_straddle = None


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
# 🔴 START STRADDLE
# =========================
def start_straddle(kite, ce_symbol, pe_symbol, qty, send_telegram):
    global active_straddle

    try:
        # 🔥 BUY BOTH LEGS (with retry)
        retry_api(lambda: kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NFO,
            tradingsymbol=ce_symbol,
            transaction_type=kite.TRANSACTION_TYPE_BUY,
            quantity=qty,
            product=kite.PRODUCT_MIS,
            order_type=kite.ORDER_TYPE_MARKET
        ))

        retry_api(lambda: kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NFO,
            tradingsymbol=pe_symbol,
            transaction_type=kite.TRANSACTION_TYPE_BUY,
            quantity=qty,
            product=kite.PRODUCT_MIS,
            order_type=kite.ORDER_TYPE_MARKET
        ))

        active_straddle = {
            "ce": ce_symbol,
            "pe": pe_symbol,
            "qty": qty,
            "start_time": time.time(),
            "max_profit": 0   # 🔥 Track max profit
        }

        send_telegram(f"📊 Straddle started\nCE: {ce_symbol}\nPE: {pe_symbol}\nQty: {qty}")
        logging.info(f"Straddle started: {ce_symbol} | {pe_symbol}")

        threading.Thread(
            target=monitor_straddle,
            args=(kite, send_telegram),
            daemon=True
        ).start()

    except Exception as e:
        logging.error(str(e))
        send_telegram(f"❌ Straddle error: {str(e)}")


# =========================
# 🔴 GET PNL (SAFE)
# =========================
def get_leg_pnl(kite, symbol):
    try:
        positions = retry_api(lambda: kite.positions())

        if not positions:
            return 0

        for p in positions["net"]:
            if p["tradingsymbol"] == symbol and p["quantity"] != 0:
                return p["pnl"]

        return 0

    except Exception as e:
        logging.error(f"PnL error: {str(e)}")
        return 0


# =========================
# 🔴 MONITOR
# =========================
def monitor_straddle(kite, send_telegram):
    global active_straddle

    while active_straddle:
        try:
            ce = active_straddle.get("ce")
            pe = active_straddle.get("pe")
            qty = active_straddle["qty"]

            ce_pnl = get_leg_pnl(kite, ce) if ce else 0
            pe_pnl = get_leg_pnl(kite, pe) if pe else 0

            total_pnl = ce_pnl + pe_pnl

            logging.info(f"Straddle | CE: {ce_pnl} PE: {pe_pnl} TOTAL: {total_pnl}")

            # =========================
            # 🔥 TRACK MAX PROFIT
            # =========================
            if total_pnl > active_straddle["max_profit"]:
                active_straddle["max_profit"] = total_pnl

            # =========================
            # 🔥 TRAILING SL (KEY EDGE)
            # =========================
            if active_straddle["max_profit"] > PROFIT_THRESHOLD:
                trail_sl = active_straddle["max_profit"] - TRAIL_GAP

                if total_pnl <= trail_sl:
                    send_telegram(f"🔻 Trailing SL HIT: {total_pnl}")
                    logging.info("Trailing SL triggered")
                    exit_all(kite, send_telegram)
                    break

            # =========================
            # 🔥 EXIT LOSER LEG (WITH CONFIRMATION)
            # =========================
            if ce and ce_pnl > PROFIT_THRESHOLD and pe:
                time.sleep(CONFIRM_DELAY)

                ce_pnl_check = get_leg_pnl(kite, ce)

                if ce_pnl_check > PROFIT_THRESHOLD:
                    exit_leg(kite, pe, qty, send_telegram)
                    active_straddle["pe"] = None
                    send_telegram("❌ PE exited after confirmation")
                    logging.info("Exited PE leg")

            if pe and pe_pnl > PROFIT_THRESHOLD and ce:
                time.sleep(CONFIRM_DELAY)

                pe_pnl_check = get_leg_pnl(kite, pe)

                if pe_pnl_check > PROFIT_THRESHOLD:
                    exit_leg(kite, ce, qty, send_telegram)
                    active_straddle["ce"] = None
                    send_telegram("❌ CE exited after confirmation")
                    logging.info("Exited CE leg")

            # =========================
            # 🔴 MAX LOSS
            # =========================
            if total_pnl <= MAX_LOSS:
                send_telegram("🛑 Straddle SL HIT")
                logging.warning("Straddle SL hit")
                exit_all(kite, send_telegram)
                break

            # =========================
            # 🔴 TIME EXIT
            # =========================
            if time.time() - active_straddle["start_time"] > 1800:
                send_telegram("⏱ Straddle time exit")
                logging.info("Time exit triggered")
                exit_all(kite, send_telegram)
                break

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            logging.error(f"Monitor error: {str(e)}")


# =========================
# 🔴 EXIT SINGLE LEG
# =========================
def exit_leg(kite, symbol, qty, send_telegram):
    if not symbol:
        return

    try:
        retry_api(lambda: kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NFO,
            tradingsymbol=symbol,
            transaction_type=kite.TRANSACTION_TYPE_SELL,
            quantity=qty,
            product=kite.PRODUCT_MIS,
            order_type=kite.ORDER_TYPE_MARKET
        ))

        send_telegram(f"❌ Exit: {symbol}")
        logging.info(f"Exited {symbol}")

    except Exception as e:
        logging.error(str(e))


# =========================
# 🔴 EXIT ALL
# =========================
def exit_all(kite, send_telegram):
    global active_straddle

    if not active_straddle:
        return

    qty = active_straddle["qty"]

    exit_leg(kite, active_straddle.get("ce"), qty, send_telegram)
    exit_leg(kite, active_straddle.get("pe"), qty, send_telegram)

    send_telegram("❌ Straddle closed")
    logging.info("Straddle fully closed")

    active_straddle = None