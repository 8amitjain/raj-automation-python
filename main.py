from datetime import datetime, timedelta
from io import StringIO
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

import pandas as pd
import numpy as np
import requests
import smtplib

API_TOKEN = "63b6695b417a00.44732303"
SENDER_EMAIL = "frontierholdings0809@gmail.com"

# eodhistoricaldata.com

print("HERE")
# Do your work here

now = datetime.now()  # current date and time
today = now.strftime("%Y-%m-%d")
start_date = now - timedelta(1000)
start_date = start_date.strftime("%Y-%m-%d")
# print(today, "D")
# print(start_date, "STD")

# Try with this https://github.com/kieran-mackle/AutoTrader/blob/main/autotrader/indicators.py
# TODO calculate a MACD
# TODO determine the direction of the divergence bullish or bearish


def run_algo(period, period_proper):
    bearish_divergence = []
    bullish_divergence = []
    with requests.Session() as s:
        api_url = f'https://eodhistoricaldata.com/api/exchange-symbol-list/NSE?api_token={API_TOKEN}'
        download = s.get(api_url)
        data = StringIO(download.content.decode('utf-8'))
        df = pd.read_csv(data)
        print(len(df.index), "TOTOSLLE")
    for symbol in df.loc[:, "Code"]:
        print(symbol)
        with requests.Session() as s:
            # print(f"https://eodhistoricaldata.com/api/eod/{symbol}.NSE?api_token={API_TOKEN}&from={start_date}&to={today}")

            api_url = f'https://eodhistoricaldata.com/api/eod/{symbol}.NSE?api_token={API_TOKEN}&from={start_date}&to={today}&period={period}&order=d'
            download = s.get(api_url)

            text = StringIO(download.content.decode('utf-8'))
            df = pd.read_csv(text)
            df = df.head(25)  # Starts at 0
            # print(df)

        # Daily MACD
        exp11_d = df['Close'].ewm(span=12, adjust=False).mean()
        exp22_d = df['Close'].ewm(span=26, adjust=False).mean()
        macd = exp11_d - exp22_d
        signal = macd.ewm(span=9, adjust=False).mean()
        exp50_d = df['Close'].ewm(span=50, adjust=False).mean()
        df['macd_hist'] = macd - signal
        df['exp11'] = exp11_d
        df['exp22'] = exp22_d
        df['exp50'] = exp50_d

        # DIVERGENCE IDENTIFICATION ON DAILY
        d_tol_m = 0.001*np.mean(df['macd_hist'])
        d_tol_p = 0
        n = 2
        crest_d = []
        trough_d = []
        for i in range(1, len(df['Date'])-1):
            if df['macd_hist'][i] > df['macd_hist'][i-1] and df['macd_hist'][i] > df['macd_hist'][i+1] and df['macd_hist'][i]>0:
                crest_d.append([i, df['Date'][i], df['macd_hist'][i], df['High'][i]])
            elif df['macd_hist'][i] < df['macd_hist'][i-1] and df['macd_hist'][i] < df['macd_hist'][i+1] and df['macd_hist'][i]<0:
                trough_d.append([i, df['Date'][i], df['macd_hist'][i], df['Low'][i]])
        crest_d = pd.DataFrame(crest_d, columns=['Index', 'Date', 'macd', 'High'])
        trough_d = pd.DataFrame(trough_d, columns=['Index', 'Date', 'macd', 'Low'])

        temp_bear_d = []
        for i in crest_d.index[1:]:
            if crest_d['macd'][i] < (crest_d['macd'][i-1]-d_tol_m) and crest_d['High'][i] > (crest_d['High'][i-1]+d_tol_p) and (crest_d['Index'][i] - crest_d['Index'][i-1]) > n:
                temp_bear_d.append([crest_d['Index'][i], crest_d['Date'][i]])
        bear_d = pd.DataFrame(temp_bear_d, columns=['Index', 'Date'])

        temp_bull_d = []
        for i in trough_d.index[1:]:
            if trough_d['macd'][i] > (trough_d['macd'][i-1]+d_tol_m) and trough_d['Low'][i] < (trough_d['Low'][i-1]-d_tol_p) and (trough_d['Index'][i] - trough_d['Index'][i-1]) > n:
                temp_bull_d.append([trough_d['Index'][i], trough_d['Date'][i]])

        bull_d = pd.DataFrame(temp_bull_d, columns=['Index', 'Date'])

        if not bull_d.empty:
            bullish_divergence.append([symbol, temp_bull_d[0][1]])

        if not bear_d.empty:
            bearish_divergence.append([symbol, temp_bear_d[0][1]])

    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.starttls()
    smtp.login(SENDER_EMAIL, "odhlzntnunatgkcn")
    msg = MIMEMultipart()
    msg['Subject'] = f"{period_proper} signal"
    msg.add_header('Content-Type', 'text/html')
    msg.attach(MIMEText(f"{period_proper} signal", 'html'))
    text_stream = StringIO()
    bullish_divergence_df = pd.DataFrame(bullish_divergence, columns=['Ticker', 'Date'])
    bullish_divergence_df.to_csv(text_stream, index=False)
    msg.attach(MIMEApplication(text_stream.getvalue(), Name=f"{period_proper} bullish_divergence signal.csv"))

    bearish_divergence_df = pd.DataFrame(bearish_divergence, columns=['Ticker', 'Date'])
    bearish_divergence_df.to_csv(text_stream, index=False)
    msg.attach(MIMEApplication(text_stream.getvalue(), Name=f"{period_proper} bearish_divergence signal.csv"))

    smtp.sendmail(SENDER_EMAIL, "8amitjain@gmail.com", msg.as_string())
    smtp.sendmail(SENDER_EMAIL, "rajveerdabriwal@gmail.com",  msg.as_string())
    smtp.quit()


# run_algo("d", "Daily")
# run_algo("w", "Weekly")
# run_algo("m", "Monthly")
