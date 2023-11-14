from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockTradesRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
from blk_utils import quantize_number
import pytz
from typing import List
import streamlit as st
from stqdm import stqdm

load_dotenv()


def get_stock_price_alpaca_iex(ticker: str):
    request_params = StockTradesRequest(
        symbol_or_symbols=[ticker],
        timeframe=TimeFrame.Minute,
        end=datetime.now(tz=pytz.timezone("US/Eastern")),
        limit=1,
        feed="iex",
    )

    data = client.get_stock_trades(request_params)

    # get price from dataframe

    price = quantize_number(data.df["price"].iloc[0])
    return price


def get_all_stock_prices(symbols: List[str]) -> pd.Series:
    price_series = pd.Series(index=symbols, name="price")

    for symbol in stqdm(symbols):
        price = get_stock_price_alpaca_iex(symbol)
        price_series.loc[symbol] = float(price)
    return price_series


api_key = st.secrets["alpaca_paper_key"]
api_secret = st.secrets["alpaca_paper_secret"]

client = StockHistoricalDataClient(api_key, api_secret)

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
