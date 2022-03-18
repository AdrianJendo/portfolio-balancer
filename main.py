import math
from ib_insync import *
import pandas as pd
import yfinance as yf
from optparse import OptionParser

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


# Currently only works in USD
def main():
    ib = IB()
    try:
        # Get new portfolio & weights
        weights_df = pd.read_excel("./portfolio/portfolio.xlsx")

        if weights_df["Weight"].sum() > 1:
            return False

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

    except:
        print("ERROR")

    return

    # use matplotlib with --options TO COMPARE PORtFOLIO PERFORMANCE against S&P AND SHOW HISTORY (MONGDB)
    # Display portfolio performance against SPY & QQQ


if __name__ == "__main__":
    # Use options parser to see if user wants to upload portfolio / rebalance, or view on chart
    # -u / -r / -v just needs to be present in command (NO ARGUMENTS AFTER)
    parser = OptionParser()
    parser.add_option(
        "-u",
        "--upload",
        action="store_true",
        default=False,
        dest="upload",
    )
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

    (options, args) = parser.parse_args()

    print(options)

    # main()


# print(weights_df.iloc[0]["Rebalance"])
# print(
#     weights_df.iloc[0].get("First Date")
# )  # If no first date, base next rebalance off of today's date
