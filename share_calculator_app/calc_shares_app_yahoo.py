from typing import List

import pandas as pd
import streamlit as st
import yfinance as yf
from blk_utils import quantize_number
from stqdm import stqdm


def get_stock_price_yahoo(ticker: str):
    end_date = pd.to_datetime("today")
    start_date = end_date - pd.Timedelta(days=2)
    prices = yf.Ticker(ticker).history(start=start_date, end=end_date)
    closes = prices.loc[:, "Close"].rename(columns=str.lower)

    # get price from dataframe

    price = quantize_number(closes["close"].iloc[-1])
    return price


def get_all_stock_prices(symbols: List[str]) -> pd.Series:
    price_series = pd.Series(index=symbols, name="price")

    for symbol in stqdm(symbols):
        price = get_stock_price_yahoo(symbol)
        price_series.loc[symbol] = float(price)
    return price_series


default_symbols = ["SPY", "QQQ", "AMD"]  # default
st.header("How many stock shares should you buy?", divider="blue")
st.write(
    "This app will calculate the number of shares you should buy or sell to rebalance your portfolio"
)
st.write(
    "All you need to do is input the starting equity, the stock symbols, portfolio weights and your current number of shares"
)

# input starting equity
equity = st.number_input(
    "Starting Equity",
    min_value=1_000.0,
    max_value=100_000_000.0,
    value=10_000.0,
    step=1000.0,
    key="equity",
)

# input starting symbols
default_str_symbols = ", ".join(default_symbols)
text_symbols = st.text_input(
    "Stock Symbols",
    value="",
    placeholder=default_str_symbols,
    max_chars=500,
)

# input weights
default_weights = ", ".join([str(x) for x in [0.4, 0.3, 0.3]])
text_weights = st.text_input(
    "Stock Weights: must be decimal",
    value="",
    placeholder=default_weights,
    max_chars=500,
)

# input num shares already owned
default_shares = ", ".join([str(x) for x in [10, 5, 1]])
text_shares = st.text_input(
    "Quantity Of Shares Already Owned",
    value="0, 0, 0",
    placeholder=default_shares,
    max_chars=500,
)

cond0 = len(text_symbols) > 0
cond1 = len(text_weights) > 0

if all([cond0, cond1]):
    symbol_list = [x.strip() for x in text_symbols.split(",")]
    weights_list = [float(x) for x in text_weights.split(",")]
    shares_list = [float(x) for x in text_shares.split(",")]

    assert (
        len(symbol_list) == len(weights_list) == len(shares_list)
    ), "number of symbols, weights, and shares must be equal!"

    weights = pd.Series(
        weights_list,
        index=symbol_list,
        name="weight",
    )

    prices = get_all_stock_prices(symbol_list)
    out = pd.concat([prices, weights], axis=1)
    out["target_shares"] = (equity * weights / prices).apply(
        quantize_number, precision=0
    )
    if len(text_shares) > 0:
        out["current_shares"] = shares_list
        out["net_shares_to_rebalance"] = out["target_shares"] - out["current_shares"]

    st.dataframe(out, use_container_width=True)
