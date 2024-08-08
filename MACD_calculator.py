import yfinance as yf
import pandas as pd
from scipy.signal import find_peaks
from datetime import datetime, timedelta
import mplfinance as mpf

def get_price_peaks_and_macd(ticker, start_date, end_date, interval):
    # Dictionary mapping tickers to their prominence values
    prominence_dict = {
        "USDJPY=X": 0.1,    # USD/JPY
        "EURUSD=X": 0.001,  # EUR/USD
        "GBPUSD=X": 0.0012,  # GBP/USD
        "AUDUSD=X": 0.001,  # AUD/USD
        "USDCAD=X": 0.001   # USD/CAD
    }

    # Get the prominence value for the given ticker
    prominence = prominence_dict.get(ticker, 0.001)  # Default to 0.001 if ticker is not in dictionary

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

    # Find peaks in the price series with prominence filtering
    peaks, _ = find_peaks(close_prices, prominence=prominence)  # Use the dynamic prominence value

    # Get the last 2 peaks
    last_2_peaks = peaks[-2:]

    # Prepare results
    peak_info = []
    for peak in last_2_peaks:
        date = data.index[peak]
        price = close_prices.iloc[peak]
        macd_value = macd_histogram.iloc[peak]  # Get MACD value at the peak
        peak_info.append({
            'Date': date,
            'Price': f"{price:.4f}",  # Format price to 4 decimal places
            'MACD': f"{macd_value:.4f}"  # Format MACD to 4 decimal places
        })

    # Get the most recent price, date, and MACD value
    most_recent = {
        'Date': data.index[-1],
        'Price': f"{close_prices.iloc[-1]:.4f}",  # Format price to 4 decimal places
        'MACD': f"{macd_histogram.iloc[-1]:.4f}"  # Format MACD to 4 decimal places
    }

    return peak_info, most_recent, data, macd_line, signal_line, macd_histogram, last_2_peaks

def plot_chart(data, macd_line, signal_line, macd_histogram, peaks):
    # Define additional plots for MACD
    macd_addplot = [
        mpf.make_addplot(macd_line, panel=1, color='blue', secondary_y=False, label='MACD Line'),
        mpf.make_addplot(signal_line, panel=1, color='orange', secondary_y=False, label='Signal Line'),
        mpf.make_addplot(macd_histogram, panel=1, type='bar', color='dimgray', secondary_y=True, label='Histogram')
    ]

    # Extract peak dates for vlines
    peak_dates = [data.index[peak] for peak in peaks]

    # Plot the candlestick chart with MACD and vertical lines at peaks
    mpf.plot(
        data,
        type='candle',
        style='yahoo',
        title='Candlestick Chart with MACD (Last 7 Days)',
        ylabel='Exchange Rate',
        volume=True,  # Add volume to the chart
        mav=(12, 26),  # Add moving averages (12 and 26-hour averages)
        figratio=(14, 7),  # Aspect ratio of the plot
        datetime_format='%b %d, %H:%M',  # Format for date-time labels
        xrotation=45,  # Rotate x-axis labels for better readability
        addplot=macd_addplot,
        vlines=dict(
            vlines=peak_dates,
            linewidths=1,
            colors='red',
            alpha=0.7
        )
    )

# Example usage
ticker = "AUDUSD=X"
start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
end_date = datetime.now().strftime('%Y-%m-%d')
interval = "1h"

# Call the function to get peaks and most recent data
peaks, recent, data, macd_line, signal_line, macd_histogram, peak_indices = get_price_peaks_and_macd(ticker, start_date, end_date, interval)

print("Last 2 Price Peaks with MACD Levels:")
for peak in peaks:
    print(f"Date: {peak['Date']}, Price: {peak['Price']}, MACD: {peak['MACD']}")

print("\nMost Recent Data:")
print(f"Date: {recent['Date']}, Price: {recent['Price']}, MACD: {recent['MACD']}")

# Plot the chart with vertical lines at peaks
plot_chart(data, macd_line, signal_line, macd_histogram, peak_indices)
