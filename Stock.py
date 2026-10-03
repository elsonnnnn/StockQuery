# Import the yfinance. If you get module not found error the run !pip install yfinance from your Jupyter notebook
import yfinance as yf
import pandas as pd
import datetime
from pathlib import Path
from curl_cffi import requests

#Function for making conversion
def convert_usd(row,usdmyr):
    if row['Country'] == 'US':
        price_myr = format(float(row['LastPrice'])*float(usdmyr),".2f")
    elif row['Country'] != 'US':
        price_myr = row['LastPrice']
    return price_myr

def get_lastprice(ticker, specified_date):

    strtDate = specified_date - datetime.timedelta(5)
    endDate = specified_date + datetime.timedelta(5)

    tickerinfo = yf.Ticker(ticker,session=session)
    ticker_historydata = tickerinfo.history(start = strtDate, end = endDate)
    ticker_historydata = ticker_historydata.reset_index()
    ticker_historydata['Date'] = pd.to_datetime(ticker_historydata['Date']).dt.date

    valid_prices = ticker_historydata[
        (ticker_historydata['Date'] <= specified_date) & ticker_historydata['Close'].notna()
    ]
    if valid_prices.empty:
        raise ValueError(f"No closing price for {ticker} on or before {specified_date} in fetched history")

    latest = valid_prices.sort_values('Date').iloc[-1]
    lastprice_date = latest['Date']
    ticker_lastprice = format(latest['Close'], ".2f")

    return ticker_lastprice, lastprice_date

def main():
    #Fix to impersonate a session, workaround for YFRateLimitError problem

    #Get ticker file to acquire tickers
    ticker_datapath = Path(__file__).resolve().parent / "ticker.csv"
    ticker_data = pd.read_csv(ticker_datapath)
    ticker_data = ticker_data[['Ticker','YF_Ticker','Country']]

    #Convert tickers into list for looping
    ticker_list = list(ticker_data['YF_Ticker'])

    #Get latest exchange rate for USD/MYR
    usdmyr = format(yf.Ticker('MYR=X',session=session).fast_info['lastPrice'],".2f")
    #usdmyr = format(yf.Ticker('MYR=X').basic_info['lastPrice'],".2f") #Feature deprecated, modified on 27Apr2025
    print(f"Date today: {datetime.date.today()}")
    print(f'USD/MYR = {usdmyr}')

    #Request Date from User
    date_input = input(f"Provide Date in YYYY-MM-DD format (Default: {datetime.date.today()}):\n")
    if date_input == '':
        specified_date = datetime.date.today()

    elif date_input != '':
        date_input = date_input.split('-')
        #Convert Input Date to Actual Date
        specified_date = datetime.date(int(date_input[0]), int(date_input[1]), int(date_input[2]))

    print(f'Date Selected: {specified_date}')

    #print(strtDate)
    #print(endDate)
    if specified_date != datetime.date.today():
        print(f'Selected Date is not today, attempt to fetch USD/MYR rate for {specified_date}...')
        usdmyr, lastprice_date = get_lastprice('MYR=X', specified_date)
        if lastprice_date != specified_date:
            print(f'Note: USD/MYR rate for {specified_date} not available, using rate for {lastprice_date} instead.')
        print(f'USD/MYR on {lastprice_date} = {usdmyr}')

    ticker_price_data = pd.DataFrame()

    #Loop through list for each tickers
    for ticker in ticker_list:
        ticker_lastprice, lastprice_date = get_lastprice(ticker, specified_date)

        #print(f'{ticker} : {ticker_lastprice}')

        ticker_data_append_dict = {'YF_Ticker' : ticker,
                                'LastPrice_Date' : lastprice_date,
                                'LastPrice' : ticker_lastprice}
        ticker_data_append_df = pd.DataFrame([ticker_data_append_dict])
        ticker_price_data = pd.concat([ticker_price_data, ticker_data_append_df], ignore_index=True)

    #print(ticker_price_data)

    ticker_data = pd.merge(ticker_data, ticker_price_data, 'left', on='YF_Ticker')
    ticker_price_data.to_csv(ticker_datapath, index=False)

    ticker_data['LastPrice(MYR)'] = ticker_data.apply(lambda row: convert_usd(row, usdmyr), axis=1)
    print(ticker_data)
    print(f'Data saved to {ticker_datapath}')
    ticker_data.to_csv(ticker_datapath, index=False)
    input('Press Enter to Exit')

if __name__ == "__main__":
    session = requests.Session(impersonate="chrome")

    main()
