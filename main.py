import math
from ib_insync import *
import pandas as pd
import yfinance as yf
from optparse import OptionParser
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
import os

API_URL = os.environ.get("API_URL")
API_KEY = os.environ.get("API_KEY")

# Use yfinance API to get price data
def get_price_data(row, shares_to_buy={}, positions={}, portfolio_value=0):
    ticker = row["Ticker"]
    weight = row["Weight"]
    stock = yf.Ticker(ticker)
    price_data = stock.history(period="max")
    last_price = round(price_data.iloc[-1]["Close"], 2)

    shares = portfolio_value * weight / last_price
    if ticker in positions:
        shares -= positions[ticker]["shares"]

    shares_to_buy[ticker] = {
        "shares": math.floor(shares),  # Fractional shares can't be placed via API
        "last_price": last_price,
    }


def validate_date(date_text):
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def get_time_delta(frequency):
    if frequency == "quarterly":
        return relativedelta(months=3)
    elif frequency == "biannually":
        return relativedelta(months=6)
    elif frequency == "annually":
        return relativedelta(years=1)
    else:  # default do monthly
        return relativedelta(months=1)


def rebalance(options, weights_df):
    ib = IB()
    try:
        # Connect to broker
        ib.connect("127.0.0.1", 7497, clientId=1)

        # Get current positions
        positions = {}
        accountSummary = ib.accountSummary()

        portfolio_value = 0
        for item in accountSummary:
            if item.tag == "CashBalance" and item.currency == "USD":
                portfolio_value += float(item.value)

        portfolio = ib.portfolio()
        for position in portfolio:
            positions[position.contract.symbol] = {
                "shares": position.position,
                "mkt_value": position.marketValue,
            }
            portfolio_value += position.marketValue

        # Close all current orders
        ib.reqGlobalCancel()

        # Calculate number of shares to buy / sell
        shares_to_buy = {}
        weights_df.apply(
            get_price_data,
            axis=1,
            shares_to_buy=shares_to_buy,
            positions=positions,
            portfolio_value=portfolio_value,
        )

        for ticker in positions:
            if ticker not in shares_to_buy:
                shares_to_buy[ticker] = {
                    "shares": -positions[ticker]["shares"],
                    "last_price": round(
                        positions[ticker]["mkt_value"] / positions[ticker]["shares"], 2
                    ),
                }

        # Fill buy/sell orders
        trades = []
        for ticker in shares_to_buy:
            contract = Stock(ticker, "SMART", "USD")
            ib.qualifyContracts(contract)
            shares = shares_to_buy[ticker]["shares"]
            buy_or_sell = "BUY" if shares > 0 else "SELL"
            order = MarketOrder(buy_or_sell, abs(shares))
            trades.append(ib.placeOrder(contract, order))

        print(trades)

        # Check if cron job exists and create one if it doesn't

    except:
        print("ERROR CONNECTING TO IB OR SUBMITTING TRADES")


def get_prices_df(start_date, all_tickers):
    end_date = datetime.now().strftime("%Y-%m-%d")
    prices_df = pd.DataFrame(columns=[])
    first_ticker = True
    for ticker in all_tickers:
        # Get price data
        price_data = requests.get(
            "{}/{}".format(API_URL, ticker),
            params={"serietype": "line", "apikey": API_KEY},
        )

        # Get dividend data
        dividend_data = requests.get(
            "{}/stock_dividend/{}".format(API_URL, ticker), params={"apikey": API_KEY}
        )

        # Parse price data
        price_data = price_data.json()["historical"]
        price_data_df = pd.DataFrame(price_data)
        price_data_df = price_data_df.set_index("date").sort_index()
        price_data_df = price_data_df.rename(columns={"close": ticker})

        # Parse dividend data
        dividend_data = dividend_data.json().get(
            "historical",
            [
                {
                    "date": end_date,
                    "adjDividend": 0,
                }  # Dummy data to avoid errors if company never paid a dividend
            ],
        )
        dividend_df = pd.DataFrame(
            [{"date": x["date"], "dividend": x["adjDividend"]} for x in dividend_data]
        )
        dividend_df = dividend_df.set_index("date").sort_index()
        dividend_df = dividend_df.rename(columns={"dividend": "{}_DIV".format(ticker)})

        # Update main df
        if first_ticker:
            prices_df = pd.concat([prices_df, price_data_df, dividend_df], axis=1)
            first_ticker = False
        else:
            prices_df = prices_df.join([price_data_df, dividend_df], how="left")

    return prices_df.loc[start_date:end_date]


def get_portfolio_value():
    pass


def graph_return(options, weights_df):
    # Compare return of rebalanced portfolio to SPY, QQQ, DIA
    start_date = options.start_date  # day to start comparison
    frequency = options.frequency  # frequency of rebalance
    cur_datetime = datetime.strptime(start_date, "%Y-%m-%d")
    next_rebalance = cur_datetime  # Next date to rebalance portfolio
    last_rebalance = cur_datetime - relativedelta(
        days=5  # 5 days to avoid weekends & program errors when last_date and start_date are same day
    )
    end_datetime = datetime.now()  # show return until today

    print(
        list(weights_df["Ticker"]),
        float(weights_df.loc[weights_df["Ticker"] == "AAPL"]["Weight"]),
    )
    portfolio_tickers = list(weights_df["Ticker"])
    all_tickers = [
        "SPY",
        "QQQ",
        "DIA",
    ] + portfolio_tickers  # compare against major indices
    prices_df = get_prices_df(start_date, all_tickers)
    return_df = pd.DataFrame(columns=["date"] + all_tickers)

    print(prices_df, return_df)

    # 1. CHANGE TO YFINANCE API AND GET RID OF REQUESTS
    # 2. GRAPH TIME
    return

    while end_datetime > cur_datetime:
        cur_date = cur_datetime.strftime("%Y-%m-%d")
        last_date = last_contribution.strftime("%Y-%m-%d")
        portfolio_value = 100  # Calculate current market value BEFORE rebalance

        # Rebalance portfolio
        if next_rebalance <= cur_datetime:
            next_rebalance += get_time_delta(frequency)
            dividend = price_df.loc[last_date:cur_date]["dividend"].sum()
            investible_dollars = contribution + remainder + dividend * num_shares
            num_shares += investible_dollars // stock_price
            total_investment += investible_dollars // stock_price * stock_price
            remainder = investible_dollars % stock_price
            last_contribution = cur_datetime

        # Update graph every 7 days
        return_summary_df = pd.concat(
            [
                return_summary_df,
                pd.DataFrame(
                    [
                        [
                            cur_date,
                            round(total_investment, 2),
                            round(num_shares * stock_price, 2),
                        ]
                    ],
                    columns=["date", "total_investment", "portfolio_value"],
                ),
            ]
        )

        cur_datetime += relativedelta(days=7)  # Update graph every 7 days

    return_summary_df = return_summary_df.set_index("date").sort_index()
    print("Start of df: ")
    print(return_summary_df.head(5))
    print("End of df: ")
    print(return_summary_df.tail(5))

    plot_df(return_summary_df, ticker)


# Currently only works in USD
def main(options):
    # Get portfolio and check if weights sum to > 100%
    weights_df = pd.read_excel("./portfolio/portfolio.xlsx")

    if weights_df["Weight"].sum() > 1:
        print("Weights sum to > 1")
        return False
    elif options.frequency and options.frequency.lower() not in [
        "monthly",
        "quarterly",
        "biannually",
        "annually",
    ]:  # Check if frequency and start date are acceptable
        print(
            'Frequency not a valid options.\nValid options are:\n["monthly", "quarterly", "biannually", "annually"]'
        )
        return False
    elif options.start_date and not validate_date(options.start_date):
        print("Incorrect format for start_date. Valid format is YY-mm-dd")

    if options.rebalance:
        rebalance(options, weights_df)
    if options.view_chart:
        graph_return(options, weights_df)


if __name__ == "__main__":
    # Use options parser to see if user wants to upload portfolio / rebalance, or view on chart
    # -u / -r / -v just needs to be present in command (NO ARGUMENTS AFTER)
    parser = OptionParser()
    parser.add_option(
        "-r",
        "--rebalance",
        action="store_true",
        default=False,
        dest="rebalance",
    )
    parser.add_option(
        "-v",
        "--view_chart",
        action="store_true",
        default=False,
        dest="view_chart",
    )
    parser.add_option(
        "-s",
        "--start_date",
        default=(datetime.now() - relativedelta(years=10)).strftime("%Y-%m-%d"),
        dest="start_date",
        help="date to start calculate",
    )
    parser.add_option(
        "-f",
        "--frequency",
        default="monthly",
        dest="frequency",
        help="frequency of recurring contribution",
    )

    (options, args) = parser.parse_args()

    main(options)
