from datetime import datetime, timedelta
from io import StringIO
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

import pandas as pd
import numpy as np
import requests
import smtplib
import time

# https://eodhistoricaldata.com/api/intraday/NSEI.INDX?api_token=63b6695b417a00.44732303

API_TOKEN = "63b6695b417a00.44732303"
SENDER_EMAIL = "frontierholdings0809@gmail.com"

# eodhistoricaldata.com

print("HERE")
# Do your work here

now = datetime.now()  # current date and time
# today = now.strftime("%Y-%m-%d")
start_date = now - timedelta(160)  # TIME FRAME
# start_date = start_date.strftime("%Y-%m-%d")
# print(today, "D")
# print(start_date, "STD")

# Try with this https://github.com/kieran-mackle/AutoTrader/blob/main/autotrader/indicators.py


def run_algo(period, period_proper):
    def check_positive(num):
        if num >= 0:
            return True
        else:
            return False

    bearish_divergence = []
    bullish_divergence = []
    with requests.Session() as s:
        api_url = f'https://eodhistoricaldata.com/api/exchange-symbol-list/INDX?api_token={API_TOKEN}'
        download = s.get(api_url)
        data = StringIO(download.content.decode('utf-8'))
        df = pd.read_csv(data)
    for symbol in df.loc[:, "Code"].head(1):
        # print(symbol)
        symbol = "NSEBANK"
        print(symbol)

        with requests.Session() as s:
            # print(f"https://eodhistoricaldata.com/api/eod/{symbol}.NSE?api_token={API_TOKEN}&from={start_date}&to={today}")

            api_url = f'https://eodhistoricaldata.com/api/intraday/NSEBANK.INDX?api_token={API_TOKEN}&from={time.mktime(start_date.timetuple())}&to={time.mktime(now.timetuple())}&interval={period_proper}'
            download = s.get(api_url)

            text = StringIO(download.content.decode('utf-8'))
            df = pd.read_csv(text)
            # df = df.tail(900)  # Starts at 0
            pd.set_option('display.max_columns', None)

            # print(df)

        # Daily MACD
        print(df.head())
        # df = df.iloc[::-1]

        exp11_d = df['Close'].ewm(span=12, adjust=False).mean()
        exp22_d = df['Close'].ewm(span=26, adjust=False).mean()
        macd = exp11_d - exp22_d
        signal = macd.ewm(span=9, adjust=False).mean()
        exp50_d = df['Close'].ewm(span=50, adjust=False).mean()
        df['macd_hist'] = macd - signal
        df['exp11'] = exp11_d
        df['exp22'] = exp22_d
        df['exp50'] = exp50_d

        df = df.iloc[::-1]
        # df = df.head(144)  # Starts at 0
        # pd.set_option('display.max_columns', None)

        # df = df.iloc[::-1]
        df = df.reset_index()

        print(df.head())

        # df.to_csv(f'APOLLOTYRE-{period_proper}-MACD.csv')

        bearish = []
        bullish = []
        bullish_macd = []
        bearish_macd = []

        # print(df.head())
        # time.sleep(5)
        for i in range(1, len(df['Datetime']) - 1):
            # print(df['macd_hist'])
            if check_positive(df['macd_hist'][i]):
                # Adding all positive values to bearish
                bearish_macd.append([i, df['Datetime'][i], df['macd_hist'][i], df['High'][i], df['Close'][i]])
            else:
                # Adding all non-positive values to bullish
                bullish_macd.append([i, df['Datetime'][i], df['macd_hist'][i], df['Low'][i], df['Close'][i]])

        bullish_macd_df = pd.DataFrame(bullish_macd, columns=['Index', 'Datetime', 'macd_hist', 'Low', 'Close'])
        bearish_macd_df = pd.DataFrame(bearish_macd, columns=['Index', 'Datetime', 'macd_hist', 'High', 'Close'])

        bullish_macd_df = bullish_macd_df.iloc[::-1]
        bearish_macd_df = bearish_macd_df.iloc[::-1]

        for i in range(1, len(bullish_macd_df['Datetime']) - 1):
            # Bullish | -6  -7  -5   | -6 >= -7 <= -5
            if bullish_macd_df['macd_hist'][i - 1] >= bullish_macd_df['macd_hist'][i] <= bullish_macd_df['macd_hist'][i + 1]:
                a = bullish_macd_df['Low'][i - 1]
                b = bullish_macd_df['Low'][i]
                c = bullish_macd_df['Low'][i + 1]
                if a < b and a < c:
                    smallest = a
                elif b < c:
                    smallest = b
                else:
                    smallest = c
                # print(a,b ,c, smallest, "BEAs")
                bullish.append([i, bullish_macd_df['Datetime'][i], bullish_macd_df['macd_hist'][i], smallest])

        for i in range(1, len(bearish_macd_df['Datetime']) - 1):
            # Bearish | 4 6 5  | 4 <= 6 >= 5
            if bearish_macd_df['macd_hist'][i - 1] <= bearish_macd_df['macd_hist'][i] >= bearish_macd_df['macd_hist'][i + 1]:
                highest = max(bearish_macd_df['High'][i - 1], bearish_macd_df['High'][i],  bearish_macd_df['High'][i + 1])
                bearish.append([i, bearish_macd_df['Datetime'][i], bearish_macd_df['macd_hist'][i], highest])

        bearish = pd.DataFrame(bearish, columns=['Index', 'Datetime', 'macd', 'High'])
        bullish = pd.DataFrame(bullish, columns=['Index', 'Datetime', 'macd', 'Low'])

        bearish = bearish.iloc[::-1]
        bullish = bullish.iloc[::-1]

        # for i in bearish.index[1:]:
        for i in range(1, len(bearish['Datetime']) - 1):
            # Bearish MACD 8 > 6 | 8  6
            # Bearish HIGH 6 < 7 | 6  7
            if bearish['macd'][i + 1] > bearish['macd'][i] and bearish['High'][i + 1] < bearish['High'][i]:
                bearish_divergence.append([symbol, bearish['Datetime'][i + 1], bearish['High'][i + 1], bearish['macd'][i + 1], bearish['Datetime'][i], bearish['High'][i], bearish['macd'][i]])

        for i in range(1, len(bullish['Datetime']) - 1):
            # Bullish MACD -9 < -7 | -9  -7
            # Bullish LOW 9 > 7 | 9  7
            if bullish['macd'][i + 1] < bullish['macd'][i] and bullish['Low'][i + 1] > bullish['Low'][i]:
                bullish_divergence.append([symbol, bullish['Datetime'][i + 1], bullish['Low'][i + 1], bullish['macd'][i + 1], bullish['Datetime'][i], bullish['Low'][i], bullish['macd'][i]])

    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.starttls()
    smtp.login(SENDER_EMAIL, "odhlzntnunatgkcn")
    msg = MIMEMultipart()
    msg['Subject'] = f"{period_proper} signal"
    msg.add_header('Content-Type', 'text/html')
    msg.attach(MIMEText(f"{period_proper} signal", 'html'))
    text_stream = StringIO()
    bullish_divergence_df = pd.DataFrame(bullish_divergence, columns=['Ticker', 'Datetime', 'Low', 'Macd', 'Datetime -2 ', 'Low -2 ', 'Macd -2'])
    bullish_divergence_df.to_csv(text_stream, index=False)
    msg.attach(MIMEApplication(text_stream.getvalue(), Name=f"{period_proper} bullish_divergence signal.csv"))

    text_stream = StringIO()
    bearish_divergence_df = pd.DataFrame(bearish_divergence, columns=['Ticker', 'Datetime', 'High', 'Macd', 'Datetime -2 ', 'High -2 ', 'Macd -2'])
    bearish_divergence_df.to_csv(text_stream, index=False)
    msg.attach(MIMEApplication(text_stream.getvalue(), Name=f"{period_proper} bearish_divergence signal.csv"))

    smtp.sendmail(SENDER_EMAIL, "8amitjain@gmail.com", msg.as_string())
    smtp.sendmail(SENDER_EMAIL, "rajveerdabriwal@gmail.com",  msg.as_string())
    smtp.quit()


run_algo("h", "1h")
