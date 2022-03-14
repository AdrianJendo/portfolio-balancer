from ib_insync import *
import pandas as pd

excel_df = pd.read_excel("./portfolio.xlsx")
print(excel_df)

print(excel_df["Weight"].sum() < 1)

print(excel_df.iloc[0]["Rebalance"])
print(
    excel_df.iloc[0].get("First Date")
)  # If no first date, base next rebalance off of today's date


# GET CURRENT POSITION


# CALCULATE NEW POSITIONS (NUMBER OF SHARES OF EACH SECURITY TO PURCHASE)


# FILL BUY/SELL ORDERS


# ib = IB()
# ib.connect("127.0.0.1", 7497, clientId=1)

# stock = Stock("AAPL", "SMART", "USD")
# bars = ib.reqHistoricalData(
#     stock,
#     endDateTime="",
#     durationStr="30 D",
#     barSizeSetting="1 hour",
#     whatToShow="MIDPOINT",
#     useRTH=True,
# )

# # convert to pandas dataframe:
# df = util.df(bars)
# print(df)

# market_data = ib.reqMktData(stock, "", False, False)
# ib.sleep(2)
# print(market_data)
