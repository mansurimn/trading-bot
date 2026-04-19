from datetime import datetime, timedelta

# =========================
# 🔴 GET WEEKLY EXPIRY (THURSDAY / FRIDAY)
# =========================
def get_weekly_expiry(instrument):
    today = datetime.now()

    # NIFTY → Thursday expiry
    if instrument == "NIFTY":
        target_weekday = 3  # Thursday

    # SENSEX → Friday expiry
    elif instrument == "SENSEX":
        target_weekday = 4  # Friday

    else:
        target_weekday = 3

    days_ahead = target_weekday - today.weekday()

    if days_ahead < 0:
        days_ahead += 7

    expiry = today + timedelta(days=days_ahead)

    # Format → 05SEP / 12JAN etc.
    return expiry.strftime("%d%b").upper()


# =========================
# 🔴 GET ATM STRIKE
# =========================
def get_atm_strike(price, instrument):

    if instrument == "NIFTY":
        return round(price / 50) * 50

    elif instrument == "SENSEX":
        return round(price / 100) * 100

    return round(price / 50) * 50


# =========================
# 🔴 BUILD OPTION SYMBOL
# =========================
def build_option_symbol(price, option_type, instrument="NIFTY"):

    strike = get_atm_strike(price, instrument)
    expiry = get_weekly_expiry(instrument)

    symbol = f"{instrument}{expiry}{strike}{option_type}"

    return symbol