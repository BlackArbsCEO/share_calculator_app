from typing import List

import pandas as pd
import streamlit as st
import yfinance as yf
from blk_utils import quantize_number
from stqdm import stqdm


def get_stock_price_yahoo(ticker: str) -> float:
    end_date = pd.to_datetime("today")
    start_date = end_date - pd.Timedelta(
        days=5
    )  # avoid issues with holidays/long weekends
    price_series = yf.Ticker(ticker).history(start=start_date, end=end_date)
    closes = price_series.loc[:, "Close"]

    # get price from dataframe

    price = quantize_number(closes.iloc[-1])
    return price


def get_all_stock_prices(symbols: List[str]) -> pd.Series:
    price_series = pd.Series(index=symbols, name="price")

    for symbol in stqdm(symbols):
        price = get_stock_price_yahoo(symbol)
        price_series.loc[symbol] = float(price)
    return price_series


symbols = ["SPY", "AMD"]

price = get_stock_price_yahoo(symbols[0])

prices = get_all_stock_prices(symbols)
