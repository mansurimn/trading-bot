import pandas as pd
import logging
from datetime import datetime

INSTRUMENT_DF = None

def load_instruments(kite):
    global INSTRUMENT_DF

    if INSTRUMENT_DF is not None:
        return INSTRUMENT_DF

    try:
        instruments = kite.instruments("NFO")
        df = pd.DataFrame(instruments)
        df = df[df["segment"] == "NFO-OPT"]

        INSTRUMENT_DF = df
        logging.info("Instrument cache loaded")

        return df

    except Exception as e:
        logging.error(str(e))
        return None


def get_nearest_expiry(df, instrument):
    today = datetime.now().date()
    df = df[df["name"] == instrument]

    expiries = sorted(df["expiry"].unique())

    for exp in expiries:
        if exp >= today:
            return exp

    return None


def get_atm_option(kite, instrument, option_type):
    try:
        df = load_instruments(kite)
        if df is None:
            return None

        index_symbol = "NSE:NIFTY 50" if instrument == "NIFTY" else "BSE:SENSEX"
        price = kite.ltp(index_symbol)[index_symbol]["last_price"]

        strike = round(price / (50 if instrument == "NIFTY" else 100)) * (50 if instrument == "NIFTY" else 100)

        expiry = get_nearest_expiry(df, instrument)
        if not expiry:
            return None

        df_filtered = df[
            (df["name"] == instrument) &
            (df["expiry"] == expiry) &
            (df["strike"] == strike) &
            (df["instrument_type"] == option_type)
        ]

        if df_filtered.empty:
            return None

        row = df_filtered.iloc[0]

        return row["tradingsymbol"]

    except Exception as e:
        logging.error(str(e))
        return None