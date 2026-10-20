# 📈 Real-Time Stock Market Dashboard

An interactive dashboard that tracks and visualizes live stock market data with
financial indicators for selected stocks.

Built as part of my training project at **Codec Technologies**.

## Features

* Live price data fetched with the **Requests** library (Yahoo Finance API, no key needed)
* Multi-stock selection (US and Indian stocks, e.g. `AAPL`, `RELIANCE.NS`)
* Interactive **Plotly** candlestick charts with volume
* Technical indicators: **SMA, EMA, Bollinger Bands, RSI, MACD**
* Simple buy/sell momentum summary per stock
* Multi-stock performance comparison (% change)
* Auto-refresh with adjustable interval
* Raw data table + CSV download

## Tech Stack

Python • Pandas • Plotly • Requests • Streamlit

## How It Works

1. `fetch\_history()` calls the API with `requests` and converts the JSON into a Pandas DataFrame.
2. `add\_indicators()` computes SMA, EMA, Bollinger Bands, RSI and MACD with Pandas.
3. `build\_chart()` draws candlesticks, volume and indicator panels with Plotly subplots.
4. Streamlit renders the UI and re-runs on a timer to simulate real-time updates.

## Run Locally

```bash
git clone https://github.com/sandeepmeena/stock-dashboard.git
cd stock-dashboard
pip install -r requirements.txt
python -m streamlit run app.py
```

## Screenshots

*!\[Dashboard](screenshots/dashboard.png)*

*!\[Chart](screenshots/chart.png)*

*!\[Compare](screenshots/compare.png)*

## Indicators Explained

|Indicator|Meaning|
|-|-|
|SMA / EMA|Moving averages showing trend direction|
|Bollinger Bands|Volatility bands around SMA (±2 std dev)|
|RSI|>70 overbought, <30 oversold|
|MACD|Momentum; MACD crossing above signal = bullish|

## Future Improvements

* Portfolio tracking, price alerts, news sentiment

## Disclaimer

For educational purposes only. Not financial advice.

## Author

**Sandeep Meena** — [LinkedIn](https://linkedin.com/in/your-profile)

