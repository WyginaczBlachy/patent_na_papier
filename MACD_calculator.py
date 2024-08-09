import yfinance as yf
import pandas as pd
from scipy.signal import find_peaks
from datetime import datetime, timedelta
from myfxbook_scrapper import get_short_percentage
import os


def get_price_peak_and_macd(ticker, start_date, end_date, interval, prominence, distance):
    # Fetch historical market data
    data = yf.download(ticker, start=start_date, end=end_date, interval=interval)

    # Extract the 'Close' prices
    close_prices = data['Close']

    # Calculate MACD
    ema_12 = close_prices.ewm(span=12, adjust=False).mean()  # 12-period EMA
    ema_26 = close_prices.ewm(span=26, adjust=False).mean()  # 26-period EMA
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()  # 9-period EMA of MACD line
    macd_histogram = macd_line - signal_line

    # Find peaks in the price series with prominence and distance filtering
    peaks, _ = find_peaks(close_prices, prominence=prominence, distance=distance)

    # Get the most recent peak
    if len(peaks) > 0:
        most_recent_peak = peaks[-1]  # Get the last peak
    else:
        # If no peaks are found, return None for peak information
        return None, None, data, macd_line, signal_line, macd_histogram

    # Prepare results for the most recent peak
    peak_info = {
        'Date': data.index[most_recent_peak],
        'Price': close_prices.iloc[most_recent_peak],  # Keep the price as a float
        'MACD': macd_histogram.iloc[most_recent_peak]  # Keep MACD as a float
    }

    # Get the most recent price, date, and MACD value
    most_recent = {
        'Date': data.index[-1],
        'Price': close_prices.iloc[-1],  # Keep the price as a float
        'MACD': macd_histogram.iloc[-1]  # Keep MACD as a float
    }

    return peak_info, most_recent


def make_df():
    tickers = ["USDJPY=X", "EURUSD=X", "GBPUSD=X", "AUDUSD=X", "USDCAD=X"]
    start_dates = [
        (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),  # 2 days back for 15m intervals
        (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),  # 10 days back for 1h intervals
        (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')  # 20 days back for 90min intervals
    ]
    intervals = ["15m", "60m", "90m"]  # Updated intervals

    # Define custom prominence and distance values for each ticker, start date, and interval
    parameters = {
        "USDJPY=X": {
            "prominence": [0.1, 0.2, 0.6],  # 15m, 1h, 90m example values
            "distance": [3, 5, 16]  # 15m, 1h, 90m example values
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
        }
    }

    results = []

    for ticker in tickers:
        ticker_name = ticker.split('=')[0]  # Remove '=X' part

        # Get the percentage of people shorting this ticker once before looping through intervals
        short_percentage_list = get_short_percentage(ticker_name)

        # Handle the short percentage list
        short_percentage = short_percentage_list[0] if short_percentage_list else None

        for i in range(len(start_dates)):
            start_date = start_dates[i]
            interval = intervals[i]
            end_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

            # Retrieve prominence and distance values for the current ticker and interval
            ticker_params = parameters.get(ticker, {})
            if not ticker_params:
                raise ValueError(f"Parameters for ticker {ticker} are not provided.")

            prominence = ticker_params.get('prominence')
            distance = ticker_params.get('distance')

            if prominence is None or distance is None:
                raise ValueError(f"Prominence and/or distance not provided for ticker {ticker}.")

            if i >= len(prominence) or i >= len(distance):
                raise IndexError(f"Index {i} out of range for prominence or distance values for ticker {ticker}.")

            prominence_value = prominence[i]
            distance_value = distance[i]

            # Get peak and MACD information
            peak_info, recent = get_price_peak_and_macd(ticker, start_date, end_date, interval, prominence_value,
                                                        distance_value)

            if peak_info is not None:
                # Calculate the price change and percentage change
                price_change = recent['Price'] - peak_info['Price']
                percentage_change = (price_change / peak_info['Price']) * 100

                # Append results as a dictionary
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
                # Append results with N/A when no peak is found
                results.append({
                    'Ticker': ticker_name,
                    'Interval': interval,
                    'LAST PEAK DATE': 'N/A',
                    'LAST PEAK PRICE': 'N/A',
                    'LAST PEAK MACD': 'N/A',
                    'RECENT PRICE DATE': recent['Date'],
                    'RECENT PRICE': f"{recent['Price']:.4f}",
                    'RECENT MACD': f"{recent['MACD']:.7f}",
                    'PRICE CHANGE': 'N/A',
                    'PERCENTAGE CHANGE': 'N/A',
                    'SHORT %': f"{short_percentage * 100:.2f}%" if short_percentage is not None else 'N/A'
                })

    # Convert results to a DataFrame
    df_results = pd.DataFrame(results)

    output_dir = r"C:\Users\2001s\PycharmProjects\Jak poznać ślicznotkę życia\csvs"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f"signals_{timestamp}.csv"
    csv_file_path = os.path.join(output_dir, csv_filename)
    df_results.to_csv(csv_file_path, index=False)


    return df_results
# Example usage
print_in_consol = make_df()

# Set display options for Pandas DataFrame to show full content
pd.set_option('display.max_columns', None)  # Show all columns
pd.set_option('display.width', 1000)  # Set the display width to 1000 characters for full content
pd.set_option('display.max_colwidth', None)  # No truncation of column content

# Print DataFrame results
print(print_in_consol)
