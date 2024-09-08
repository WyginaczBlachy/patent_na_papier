import yfinance as yf
import pandas as pd
from scipy.signal import find_peaks
from datetime import datetime, timedelta
from myfxbook_scrapper import get_short_percentage
import os
import schedule
import time

def get_price_peak_and_macd(ticker, start_date, end_date, interval, prominence, distance):
    data = yf.download(ticker, start=start_date, end=end_date, interval=interval)

    close_prices = data['Close']

    ema_12 = close_prices.ewm(span=12, adjust=False).mean()
    ema_26 = close_prices.ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_histogram = macd_line - signal_line

    peaks, _ = find_peaks(close_prices, prominence=prominence, distance=distance)

    if len(peaks) > 0:
        most_recent_peak = peaks[-1]
    else:
        return None, None

    peak_info = {
        'Date': data.index[most_recent_peak],
        'Price': close_prices.iloc[most_recent_peak],
        'MACD': macd_histogram.iloc[most_recent_peak]
    }

    most_recent = {
        'Date': data.index[-1],
        'Price': close_prices.iloc[-1],
        'MACD': macd_histogram.iloc[-1]
    }

    return peak_info, most_recent


def make_df():
    tickers = ["USDJPY=X", "EURUSD=X", "GBPUSD=X", "AUDUSD=X", "USDCAD=X"]
    start_dates = [
        (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
        (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
        (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')
    ]
    intervals = ["15m", "60m", "90m"]

    parameters = {
        "USDJPY=X": {
            "prominence": [0.1, 0.2, 0.6],
            "distance": [3, 5, 16]
        },
        "EURUSD=X": {
            "prominence": [0.0002, 0.0007, 0.002],
            "distance": [3, 5, 16]
        },
        "GBPUSD=X": {
            "prominence": [0.0004, 0.0007, 0.0007],
            "distance": [3, 8, 16]
        },
        "AUDUSD=X": {
            "prominence": [0.0001, 0.0007, 0.0007],
            "distance": [3, 5, 16]
        },
        "USDCAD=X": {
            "prominence": [0.0003, 0.0009, 0.0009],
            "distance": [3, 5, 16]
        },
        "USDPLN=X": {
            "prominence": [0.003, 0.007, 0.007],
            "distance": [3, 5, 16]
        }
    }

    results = []

    for ticker in tickers:
        ticker_name = ticker.split('=')[0]
        short_percentage_list = get_short_percentage(ticker_name)
        short_percentage = short_percentage_list[0] if short_percentage_list else None

        for i in range(len(start_dates)):
            start_date = start_dates[i]
            interval = intervals[i]
            end_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

            ticker_params = parameters.get(ticker, {})
            prominence = ticker_params.get('prominence')
            distance = ticker_params.get('distance')
            prominence_value = prominence[i]
            distance_value = distance[i]

            peak_info, recent = get_price_peak_and_macd(ticker, start_date, end_date, interval, prominence_value, distance_value)

            if peak_info is not None and recent is not None:
                price_change = recent['Price'] - peak_info['Price']
                percentage_change = (price_change / peak_info['Price']) * 100

                results.append({
                    'Ticker': ticker_name,
                    'Interval': interval,
                    'LAST PEAK DATE': peak_info['Date'],
                    'LAST PEAK PRICE': f"{peak_info['Price']:.4f}",
                    'LAST PEAK MACD': f"{peak_info['MACD']:.7f}",
                    'RECENT PRICE DATE': recent['Date'],
                    'RECENT PRICE': f"{recent['Price']:.4f}",
                    'RECENT MACD': f"{recent['MACD']:.7f}",
                    'PRICE CHANGE': f"{price_change:.4f}",
                    'PERCENTAGE CHANGE': f"{percentage_change:.2f}%",
                    'SHORT %': f"{short_percentage * 100:.2f}%" if short_percentage is not None else 'N/A'
                })
            else:
                results.append({
                    'Ticker': ticker_name,
                    'Interval': interval,
                    'LAST PEAK DATE': 'N/A',
                    'LAST PEAK PRICE': 'N/A',
                    'LAST PEAK MACD': 'N/A',
                    'RECENT PRICE DATE': 'N/A' if recent is None else recent['Date'],
                    'RECENT PRICE': 'N/A' if recent is None else f"{recent['Price']:.4f}",
                    'RECENT MACD': 'N/A' if recent is None else f"{recent['MACD']:.7f}",
                    'PRICE CHANGE': 'N/A',
                    'PERCENTAGE CHANGE': 'N/A',
                    'SHORT %': f"{short_percentage * 100:.2f}%" if short_percentage is not None else 'N/A'
                })

    df_results = pd.DataFrame(results)

    output_dir = r"C:\Users\2001s\PycharmProjects\Jak poznać ślicznotkę życia\csvs"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f"signals_{timestamp}.csv"
    csv_file_path = os.path.join(output_dir, csv_filename)
    df_results.to_csv(csv_file_path, index=False)

    return df_results

def job():
    print(f"Starting signal retrieval at {datetime.now()}...")

    df_results = make_df()

    print(df_results)
job()

interval_minutes = 5
schedule.every(interval_minutes).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)