import math
from ib_insync import *
import pandas as pd
import yfinance as yf

# GET THESE FROM INTERACTIVE BROKERS
CUR_POSITIONS_TEMP = {
    "AMD": {"shares": 27.43, "mkt_value": 2998.92},
    "NVDA": {"shares": 4.35, "mkt_value": 999.33},
    "AAPL": {"shares": 19.34, "mkt_value": 2999.44},
    "AMZN": {"shares": 0.33, "mkt_value": 972.62},
    "FB": {"shares": 5.2, "mkt_value": 998.56},
    "GOOGL": {"shares": 1, "mkt_value": 2500},
}

PORTFOLIO_VALUE = (
    sum([position["mkt_value"] for position in CUR_POSITIONS_TEMP.values()]) + 1000
)  # Just add 1000 for cash for now

# Use yfinance API to get price data
def get_price_data(row, shares_to_buy={}):
    ticker = row["Ticker"]
    weight = row["Weight"]
    stock = yf.Ticker(ticker)
    price_data = stock.history(period="max")
    last_price = round(price_data.iloc[-1]["Close"], 2)

    shares = PORTFOLIO_VALUE * weight / last_price
    if ticker in CUR_POSITIONS_TEMP:
        shares -= CUR_POSITIONS_TEMP[ticker]["shares"]

    shares_to_buy[ticker] = {
        "shares": math.floor(shares * 1e2) / 1e2,
        "last_price": last_price,
    }

    # print(stock.info)
    # print(stock.actions)
    # print(stock.dividends)
    # print(stock.financials)
    # print(stock.quarterly_balance_sheet)
    # print(stock.earnings)
    # print(stock.cashflow)
    # print(stock.major_holders)
    # print(stock.institutional_holders)
    # print(stock.calendar)


def main():
    weights_df = pd.read_excel("./portfolio.xlsx")

    if weights_df["Weight"].sum() > 1:
        return False

    # GET CURRENT POSITIONS
    # cur_positions =

    # CALCULATE NEW POSITIONS (NUMBER OF SHARES OF EACH SECURITY TO PURCHASE)
    shares_to_buy = {}
    weights_df.apply(get_price_data, axis=1, shares_to_buy=shares_to_buy)

    for ticker in CUR_POSITIONS_TEMP:
        if ticker not in shares_to_buy:
            shares_to_buy[ticker] = -CUR_POSITIONS_TEMP[ticker]["shares"]

    # FILL BUY/SELL ORDERS

    # FRONTEND TO COMPARE PORtFOLIO PERFORMANCE AND SHOW HISTORY (MONGDB)
    # User mongo db to store portfolio value over time (take a snapshot every week or )
    # Display portfolio performance against SPY or something on simple frontend


if __name__ == "__main__":
    main()


# print(weights_df.iloc[0]["Rebalance"])
# print(
#     weights_df.iloc[0].get("First Date")
# )  # If no first date, base next rebalance off of today's date


# ------------------------------------------------------------------------------------------------------------------------------------


# ib = IB()
# ib.connect("127.0.0.1", 7497, clientId=1)

# nflx_contract = Stock("NFLX", "SMART", "USD")
# ib.qualifyContracts(nflx_contract)
# data = ib.reqMktData(nflx_contract)
# x = data.marketPrice()
# print("x", x)
# print(data)

# print(ib.portfolio())


# print(ib.trades())
# print(ib.orders())
# print(ib.openOrders())
# print(ib.openTrades())
# print(ib.fills())
# print(ib.accountSummary())
# sum(fill.commissionReport.commission for fill in ib.fills())


# ticker = ib.reqMktData(nflx_contract, "258")
# ib.sleep(2)
# print(ticker.fundamentalRatios)

# historical_data_nflx = ib.reqHistoricalData(
#     nflx_contract,
#     "",
#     barSizeSetting="15 mins",
#     durationStr="2 D",
#     whatToShow="MIDPOINT",
#     useRTH=True,
# )
# print(historical_data_nflx)

# nflx_order = MarketOrder("BUY", 200)
# trade = ib.placeOrder(nflx_contract, nflx_order)
# print(trade, trade.orderStatus.status)

# # stock = Stock("AAPL", "SMART", "USD")
# bars = ib.reqHistoricalData(
#     nflx_contract,
#     endDateTime="",
#     durationStr="30 D",
#     barSizeSetting="1 hour",
#     whatToShow="MIDPOINT",
#     useRTH=True,
# )
# print(bars)

# # convert to pandas dataframe:
# df = util.df(bars)
# print(df)

# market_data = ib.reqMktData(stock, "", False, False)
# ib.sleep(2)
# print(market_data)

# ib.run()
