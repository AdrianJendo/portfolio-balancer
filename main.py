import math
from ib_insync import *
import pandas as pd
import yfinance as yf
from optparse import OptionParser
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
import os

# Use yfinance API to get price data
def get_price_data(row, shares_needed={}, positions={}, portfolio_value=0):
    ticker = row["Ticker"]
    weight = row["Weight"]
    stock = yf.Ticker(ticker)
    price_data = stock.history(period="max")
    last_price = round(price_data.iloc[-1]["Close"], 2)

    shares = portfolio_value * weight / last_price
    if ticker in positions:
        shares -= positions[ticker]["shares"]

    shares_needed[ticker] = {
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


def ib_rebalance(options, weights_df):
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


def get_prices_df(start_date, tickers):
    prices_df = pd.DataFrame(columns=[])
    for ticker in tickers:
        # Get price data
        stock = yf.Ticker(ticker)
        price_data_df = stock.history(period="max")

        # Parse price data
        if price_data_df.empty:
            print("ERR", price_data_df)
            return pd.DataFrame()
        price_data_df = price_data_df.rename(
            columns={"Close": ticker, "Dividends": "{}_DIV".format(ticker)}
        )

        # Update main df
        print(price_data_df[[ticker, "{}_DIV".format(ticker)]], prices_df)
        prices_df = prices_df.join(
            [price_data_df[[ticker, "{}_DIV".format(ticker)]]], how="outer"
        )

    return prices_df.loc[start_date:]


def plot_df(df):
    plot = df.plot(figsize=(20, 10))
    plot.set_ylabel("% Return")
    plot.set_title("Investment Return Summary")
    plot.legend(loc="upper left")
    date_today = datetime.today().strftime("%Y-%m-%d")
    plot.figure.savefig("graphs/{}-{}.jpg".format("portfolio_return_graph", date_today))


def graph_return(options, weights_df):
    # Compare return of rebalanced portfolio to SPY, QQQ, DIA
    start_date = options.start_date  # day to start comparison
    frequency = options.frequency  # frequency of rebalance

    # print(
    #     list(weights_df["Ticker"]),
    #     float(weights_df.loc[weights_df["Ticker"] == "AAPL"]["Weight"]),
    # )
    portfolio_tickers = list(weights_df["Ticker"])
    index_tickers = ["SPY", "QQQ", "DIA"]

    print(portfolio_tickers)

    port_prices_df = get_prices_df(start_date, portfolio_tickers)
    print(port_prices_df)
    return
    index_prices_df = get_prices_df(start_date, index_tickers)
    if index_prices_df.empty:
        return
    return_df_columns = ["date", "portfolio"] + index_tickers
    return_df = pd.DataFrame(columns=return_df_columns)

    print(index_prices_df, return_df)
    print(
        "------------------------------------------------------------------------------------------------------------------------"
    )

    cur_datetime = datetime.strptime(index_prices_df.first_valid_index(), "%Y-%m-%d")
    next_rebalance = cur_datetime  # Next date to rebalance portfolio
    last_rebalance = cur_datetime - relativedelta(
        days=5  # 5 days to avoid weekends & program errors when last_date and start_date are same day
    )
    end_datetime = datetime.now()  # show return until today
    while end_datetime > cur_datetime:
        cur_date = cur_datetime.strftime("%Y-%m-%d")
        last_date = last_rebalance.strftime("%Y-%m-%d")

        # Rebalance portfolio
        if next_rebalance <= cur_datetime:
            dividend = index_prices_df.loc[
                last_date:cur_date
            ].sum()  # Assume fractional (so don't keep a remainder count)
            for ticker in index_tickers:
                if ticker in index_prices_df.columns:
                    index_prices_df[ticker][cur_date:] += dividend[
                        "{}_DIV".format(ticker)
                    ]
            last_rebalance = next_rebalance
            next_rebalance += get_time_delta(frequency)

        # Calculate returns
        print(cur_date, last_date)
        index_return = index_prices_df[:cur_date].iloc[-1] / index_prices_df.iloc[0]
        print(index_return)
        date_actual = index_prices_df[last_date:cur_date].index[-1]

        # Update graph every 5 days
        return_df = pd.concat(
            [
                return_df,
                pd.DataFrame(
                    [
                        [
                            date_actual,
                            0,
                        ]
                        + [round(index_return[index], 4) - 1 for index in index_tickers]
                    ],
                    columns=return_df_columns,
                ),
            ]
        )

        cur_datetime += relativedelta(days=5)  # Update graph every 5 days

    return_df = return_df.set_index("date").sort_index()
    print("Start of df: ")
    print(return_df.head(5))
    print("End of df: ")
    print(return_df.tail(5))

    plot_df(return_df)
    return return_df


# Currently only works in USD
def main(options):
    # Get portfolio and check if weights sum to > 100%
    weights_df = pd.read_excel("./portfolio/{}.xlsx".format(options.portfolio))

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
        ib_rebalance(options, weights_df)
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
    parser.add_option(
        "-p",
        "--portfolio",
        default="portfolio",
        dest="portfolio",
        help="name of portfolio excel file",
    )

    (options, args) = parser.parse_args()

    main(options)
