from datetime import datetime, timedelta
from io import StringIO
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from termcolor import colored as cl
import matplotlib.pyplot as plt

import pandas as pd
import numpy as np
import requests
import smtplib

plt.rcParams['figure.figsize'] = (20, 10)
plt.style.use('fivethirtyeight')

API_TOKEN = "63b6695b417a00.44732303"
SENDER_EMAIL = "frontierholdings0809@gmail.com"


print("HERE")

now = datetime.now()  # current date and time
today = now.strftime("%Y-%m-%d")
start_date = now - timedelta(1000)
start_date = start_date.strftime("%Y-%m-%d")


def run_algo(period, period_proper):

    def check_positive(num):
        if num >= 0:
            return True
        else:
            return False

    bearish_divergence = []
    bullish_divergence = []
    with requests.Session() as s:
        api_url = f'https://eodhistoricaldata.com/api/exchange-symbol-list/NSE?api_token={API_TOKEN}'
        download = s.get(api_url)
        data = StringIO(download.content.decode('utf-8'))
        df = pd.read_csv(data)
        # print(len(df.index), "total len")
    # for symbol in df.loc[:, "Code"]:
    #     print(symbol)
    with requests.Session() as s:

        # print(f"https://eodhistoricaldata.com/api/eod/APOLLOTYRE.NSE?api_token={API_TOKEN}&from={start_date}&to={today}")

        # api_url = f'https://eodhistoricaldata.com/api/eod/{symbol}.NSE?api_token={API_TOKEN}&from={start_date}&to={today}&period={period}&order=d'
        api_url = f'https://eodhistoricaldata.com/api/eod/AKG.NSE?api_token={API_TOKEN}&from={start_date}&to={today}&period={period}&order=d'
        download = s.get(api_url)

        text = StringIO(download.content.decode('utf-8'))
        df = pd.read_csv(text)
        df = df.head(300)  # Starts at 0
        # print(df)

    # Daily MACD
    df = df.iloc[::-1]
    exp11_d = df['Close'].ewm(span=12, adjust=False, min_periods=12).mean()
    exp22_d = df['Close'].ewm(span=26, adjust=False, min_periods=26).mean()
    macd = exp11_d - exp22_d
    signal = macd.ewm(span=9, adjust=False, min_periods=9).mean()
    df['macd_hist'] = macd - signal
    df['exp11'] = exp11_d
    df['exp22'] = exp22_d

    df = df.iloc[::-1]
    df = df.head(15)  # Starts at 0

    # df.to_csv('applo-daily MACD.csv')

    trough = []
    peaks = []
    print(df)
    # print(len(df['Date']))
    peaks_macd = []
    trough_macd = []
    for i in range(1, len(df['Date'])-1):
        # 5                       6                   7            |             6.5                           5.5
        # 4                      5                   6                |             4.5                           3.5
        # Bullish
        # if df['macd_hist'][i-1] <= df['macd_hist'][i] <= df['macd_hist'][i+1] and
        # df['macd_hist'][i+1] >= df['macd_hist'][i+2] >= df['macd_hist'][i+3]:
        #     peaks.append([i, df['Date'][i], df['macd_hist'][i], df['Close'][i]])

        if check_positive(df['macd_hist'][i]):
            peaks_macd.append([i, df['Date'][i], df['macd_hist'][i], df['Low'][i], df['Close'][i]])

        else:
            trough_macd.append([i, df['Date'][i], df['macd_hist'][i], df['High'][i], df['Close'][i]])

    peaks_macd_df = pd.DataFrame(peaks_macd, columns=['Index', 'Date', 'macd_hist', 'Low', 'Close'])
    peaks_macd_df.to_csv('peaks_macd_df.csv')

    trough_macd_df = pd.DataFrame(trough_macd, columns=['Index', 'Date', 'macd_hist', 'High', 'Close'])
    trough_macd_df.to_csv('trough_macd.csv')

    for i in range(1, len(peaks_macd_df['Date']) - 1):
        if peaks_macd_df['macd_hist'][i - 1] <= peaks_macd_df['macd_hist'][i] >= peaks_macd_df['macd_hist'][i + 1]:
            peaks.append([i, peaks_macd_df['Date'][i], peaks_macd_df['macd_hist'][i], peaks_macd_df['Low'][i]])

    for i in range(1, len(trough_macd_df['Date']) - 1):
        if trough_macd_df['macd_hist'][i - 1] >= trough_macd_df['macd_hist'][i] <= trough_macd_df['macd_hist'][i + 1]:
            trough.append([i, trough_macd_df['Date'][i], trough_macd_df['macd_hist'][i], trough_macd_df['High'][i]])

        # 8                7                       6                     |  7 8
        # Bearish
        # if df['macd_hist'][i-1] >= df['macd_hist'][i] >= df['macd_hist'][i+1]
        # and df['macd_hist'][i+1] <= df['macd_hist'][i+2] <= df['macd_hist'][i+3]:
        #     trough.append([i, df['Date'][i], df['macd_hist'][i], df['Close'][i]])

    trough = pd.DataFrame(trough, columns=['Index', 'Date', 'macd', 'High'])
    peaks = pd.DataFrame(peaks, columns=['Index', 'Date', 'macd', 'Low'])

    # Bearish
    #   1  2   3  4 5  index
    #   5  4   3  <4 5>  macd
    #   10 20  30   # Price
    #
    for i in trough.index[1:]:
        # if check_positive(trough['macd'][i-1]) and check_positive(trough['macd'][i]):
        if trough['macd'][i-1] > trough['macd'][i] and trough['High'][i-1] < trough['High'][i]:
            bearish_divergence.append(["APOLLOTYRE", trough['Date'][i], trough['High'][i]])

    # Bullish
    #   1  2   3  4 5  index
    #   -3  -2  -1  <3 2>  macd
    #   30 20  10   # Price
    for i in peaks.index[1:]:
        # if check_positive(peaks['macd'][i-1]) is False and check_positive(peaks['macd'][i]) is False:
        if peaks['macd'][i-1] > peaks['macd'][i] and peaks['Low'][i-1] > peaks['Low'][i]:
            bullish_divergence.append(["APOLLOTYRE", peaks['Date'][i], peaks['Low'][i]])

    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.starttls()
    smtp.login(SENDER_EMAIL, "odhlzntnunatgkcn")
    msg = MIMEMultipart()
    msg['Subject'] = f"{period_proper} signal"
    msg.add_header('Content-Type', 'text/html')
    msg.attach(MIMEText(f"{period_proper} signal", 'html'))
    text_stream = StringIO()
    bullish_divergence_df = pd.DataFrame(bullish_divergence, columns=['Ticker', 'Date', 'Low'])
    bullish_divergence_df.to_csv(text_stream, index=False)
    msg.attach(MIMEApplication(text_stream.getvalue(), Name=f"{period_proper} bullish_divergence signal.csv"))

    text_stream = StringIO()
    bearish_divergence_df = pd.DataFrame(bearish_divergence, columns=['Ticker', 'Date', 'High'])
    bearish_divergence_df.to_csv(text_stream, index=False)
    msg.attach(MIMEApplication(text_stream.getvalue(), Name=f"{period_proper} bearish_divergence signal.csv"))

    smtp.sendmail(SENDER_EMAIL, "8amitjain@gmail.com", msg.as_string())
    # smtp.sendmail(SENDER_EMAIL, "rajveerdabriwal@gmail.com",  msg.as_string())
    smtp.quit()




run_algo("d", "Daily")
# run_algo("w", "Weekly")ß
# run_algo("m", "Monthly")
