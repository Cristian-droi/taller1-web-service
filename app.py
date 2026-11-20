"""Flask web service that exposes read_value_yf over HTTP."""
import re
from datetime import date, datetime

from flask import Flask, jsonify, render_template_string, request

import read_value_yf

app = Flask(__name__)

TICKER_PATTERN = re.compile(r"^[A-Za-z0-9.\-^=]{1,15}$")

PAGE = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Stock Market Service - {{ ticker }}</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; color: #1f2933; }
    table { border-collapse: collapse; font-size: .85rem; }
    th, td { border: 1px solid #cbd2d9; padding: .3rem .6rem; text-align: right; }
    .avg { font-size: 1.3rem; margin: 1rem 0; }
    .error { color: #b91c1c; }
    code { background: #f0f4f8; padding: .1rem .3rem; }
  </style>
</head>
<body>
  <h1>Stock Market Service: {{ ticker }}</h1>
  <p>Periodo: {{ start }} a {{ end }}</p>
  {% if average is none %}
    <p class="error">No se obtuvieron datos para {{ ticker }} en ese periodo.</p>
  {% else %}
    <p class="avg">Precio de cierre promedio: <strong>{{ average }}</strong></p>
    <h2>Ultimos 10 registros</h2>
    {{ table | safe }}
  {% endif %}
  <p>Prueba otro ticker: <code>/stock/AMZN?start=2024-01-01&amp;end=2024-12-31</code>
     &middot; JSON: <code>/api/stock/AMZN</code> &middot; Salud: <code>/health</code></p>
  <p><small>Servido el {{ now }}</small></p>
</body>
</html>"""


def _parse_date(value: str | None, default: str) -> str:
    if not value:
        return default
    datetime.strptime(value, "%Y-%m-%d")  # raises ValueError when invalid
    return value


def _query(ticker: str):
    if not TICKER_PATTERN.match(ticker):
        return None, ("Invalid ticker", 400)
    try:
        start = _parse_date(request.args.get("start"), read_value_yf.DEFAULT_START_DATE)
        end = _parse_date(request.args.get("end"), date.today().isoformat())
    except ValueError:
        return None, ("Dates must use the YYYY-MM-DD format", 400)
    try:
        data = read_value_yf.get_stock_data(start, ticker.upper(), end)
    except Exception as exc:  # upstream (Yahoo Finance) failure
        app.logger.warning("Yahoo Finance request failed for %s: %s", ticker, exc)
        return None, ("Upstream data provider unavailable", 502)
    return (ticker.upper(), start, end, data), None


@app.route("/")
def index():
    return stock(read_value_yf.DEFAULT_TICKER)


@app.route("/stock/<ticker>")
def stock(ticker):
    result, error = _query(ticker)
    if error:
        return error
    ticker, start, end, data = result
    return render_template_string(
        PAGE,
        ticker=ticker,
        start=start,
        end=end,
        average=read_value_yf.average_close(data),
        table=data.tail(10).round(2).to_html(),
        now=datetime.now().isoformat(timespec="seconds"),
    )


@app.route("/api/stock/<ticker>")
def stock_api(ticker):
    result, error = _query(ticker)
    if error:
        return jsonify(error=error[0]), error[1]
    ticker, start, end, data = result
    average = read_value_yf.average_close(data)
    if average is None:
        return jsonify(ticker=ticker, start=start, end=end, error="No data returned"), 502
    return jsonify(
        ticker=ticker,
        start=start,
        end=end,
        records=len(data),
        average_close=average,
        last_close=round(float(data["Close"].iloc[-1]), 2),
    )


@app.route("/health")
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    print(f"{datetime.now()}")
    app.run(host="0.0.0.0", port=5000)
