"""Stock market data access built on top of the Yahoo Finance service (yfinance).

Can be used as a library (imported by app.py) or as a CLI script:

    python read_value_yf.py            # GOOGL
    python read_value_yf.py AMZN       # any ticker
"""
import sys
from datetime import date

import pandas as pd
import yfinance as yf

DEFAULT_TICKER = "GOOGL"
DEFAULT_START_DATE = "2020-01-01"


def get_stock_data(sd: str, stock: str, ed: str | None = None) -> pd.DataFrame:
    """Return daily price data for `stock` between `sd` and `ed` (YYYY-MM-DD).

    When `ed` is not given, today's date is used.
    """
    end = ed or date.today().isoformat()
    # Ticker.history returns single-level columns (Open, High, Low, Close, Volume...),
    # which is simpler to handle than yf.download's MultiIndex output.
    data = yf.Ticker(stock).history(start=sd, end=end, auto_adjust=False)
    return data


def average_close(data: pd.DataFrame) -> float | None:
    """Average closing price of the period, or None when there is no data."""
    if data.empty or "Close" not in data:
        return None
    return round(float(data["Close"].mean()), 2)


def test(ticker: str = DEFAULT_TICKER) -> pd.DataFrame:
    return get_stock_data(DEFAULT_START_DATE, ticker)


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) == 2 else DEFAULT_TICKER
    print(f"Retrieving stock data for {ticker}")
    data = test(ticker)
    print(data.tail())
    print(f"Average close since {DEFAULT_START_DATE}: {average_close(data)}")
