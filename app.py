(import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import plotly.graph_objects as go

# App Title
st.set_page_config(page_title="StockFinder", layout="wide")
st.title("📈 StockFinder - Nifty 500 Stock Screener")

# Date Range
end_date = datetime.datetime.today()
start_date = end_date - datetime.timedelta(days=365)

# Nifty 500 symbols from NSE (you can replace or expand this)
nifty_500_symbols = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS"
]

# Timeframe mapping
interval_map = {
    "1H": "60m",
    "2H": "120m",
    "3H": "180m",
    "4H": "240m",
    "Daily": "1d",
    "Monthly": "1mo"
}

# Indicator selection
st.sidebar.header("📊 Filter Settings")
selected_timeframe = st.sidebar.selectbox("Select Timeframe", list(interval_map.keys()))
selected_indicator = st.sidebar.selectbox("Select Indicator", ["20 EMA", "30 SMA", "200 EMA"])
setup = st.sidebar.selectbox("Select Setup", [
    "200 EMA Support + Green Candle",
    "30 SMA Support + Green Candle",
    "Monthly Breakout (Prev High)"
])

def calculate_indicators(df):
    df["20 EMA"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["30 SMA"] = df["Close"].rolling(window=30).mean()
    df["200 EMA"] = df["Close"].ewm(span=200, adjust=False).mean()
    return df

def is_support_candle(df, index, indicator_col):
    close = df.loc[index, "Close"]
    indicator = df.loc[index, indicator_col]
    prev_close = df.loc[index - 1, "Close"]
    return close > prev_close and abs(close - indicator) / indicator < 0.01

def check_setup(df, setup_type):
    if setup_type == "Monthly Breakout (Prev High)":
        return df["Close"].iloc[-1] > df["High"].iloc[-2]
    
    if setup_type in ["200 EMA Support + Green Candle", "30 SMA Support + Green Candle"]:
        ind_col = "200 EMA" if "200 EMA" in setup_type else "30 SMA"
        for i in range(1, len(df)):
            if is_support_candle(df, i, ind_col):
                return True
    return False

def plot_chart(df, symbol, indicator):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Candlestick'
    ))
    if indicator in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[indicator], line=dict(color='orange', width=2), name=indicator))
    fig.update_layout(title=symbol, height=400, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

progress = st.empty()
matches = []

for idx, symbol in enumerate(nifty_500_symbols):
    progress.text(f"Scanning: {symbol} ({idx + 1}/{len(nifty_500_symbols)})")
    try:
        data = yf.download(symbol, start=start_date, end=end_date, interval=interval_map[selected_timeframe])
        if data.empty or len(data) < 30:
            continue
        data = calculate_indicators(data)
        if check_setup(data, setup):
            matches.append((symbol, data))
    except Exception as e:
        st.write(f"Error fetching data for {symbol}: {e}")

progress.empty()

# Display Results
if matches:
    st.success(f"Found {len(matches)} matching stock(s):")
    for symbol, df in matches:
        st.subheader(symbol)
        plot_chart(df, symbol, selected_indicator)
else:
    st.warning("No matching stocks found with the selected criteria.")
