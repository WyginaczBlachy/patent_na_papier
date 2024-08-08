import yfinance as yf
from scipy.signal import find_peaks
from datetime import datetime, timedelta
import mplfinance as mpf

def get_price_peak_and_macd(ticker, start_date, end_date, interval):
    # Dictionary mapping tickers to their prominence values
    prominence_dict = {
        "USDJPY=X": 0.1,    # USD/JPY
        "EURUSD=X": 0.001,  # EUR/USD
        "GBPUSD=X": 0.001,  # GBP/USD
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

    # Get the most recent peak
    if len(peaks) > 0:
        most_recent_peak = peaks[-1]  # Get the last peak
    else:
        # If no peaks are found, return None for peak information
        return None, None, data, macd_line, signal_line, macd_histogram, None

    # Prepare results for the most recent peak
    peak_info = {
        'Date': data.index[most_recent_peak],
        'Price': f"{close_prices.iloc[most_recent_peak]:.4f}",  # Format price to 4 decimal places
        'MACD': f"{macd_histogram.iloc[most_recent_peak]:.4f}"  # Format MACD to 4 decimal places
    }

    # Get the most recent price, date, and MACD value
    most_recent = {
        'Date': data.index[-1],
        'Price': f"{close_prices.iloc[-1]:.4f}",  # Format price to 4 decimal places
        'MACD': f"{macd_histogram.iloc[-1]:.4f}"  # Format MACD to 4 decimal places
    }

    return peak_info, most_recent, data, macd_line, signal_line, macd_histogram, most_recent_peak

def plot_chart(data, macd_line, signal_line, macd_histogram, peak):
    # Define additional plots for MACD
    macd_addplot = [
        mpf.make_addplot(macd_line, panel=1, color='blue', secondary_y=False, label='MACD Line'),
        mpf.make_addplot(signal_line, panel=1, color='orange', secondary_y=False, label='Signal Line'),
        mpf.make_addplot(macd_histogram, panel=1, type='bar', color='dimgray', secondary_y=True, label='Histogram')
    ]

    # Extract peak date for vlines
    peak_date = data.index[peak] if peak is not None else None

    # Plot the candlestick chart with MACD and vertical line at the peak
    mpf.plot(
        data,
        type='candle',
        style='yahoo',
        title='Candlestick Chart with MACD (Last 10 Days)',
        ylabel='Exchange Rate',
        volume=True,  # Add volume to the chart
        mav=(12, 26),  # Add moving averages (12 and 26-hour averages)
        figratio=(14, 7),  # Aspect ratio of the plot
        datetime_format='%b %d, %H:%M',  # Format for date-time labels
        xrotation=45,  # Rotate x-axis labels for better readability
        addplot=macd_addplot,
        vlines=dict(
            vlines=[peak_date] if peak_date is not None else [],  # Only add vertical line if peak_date is valid
            linewidths=1,
            colors='red',
            alpha=0.7
        )
    )

# Example usage
ticker = "EURUSD=X"
start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
end_date = datetime.now().strftime('%Y-%m-%d')
interval = "1h"

# Call the function to get the most recent peak and most recent data
peak_info, recent, data, macd_line, signal_line, macd_histogram, peak_index = get_price_peak_and_macd(ticker, start_date, end_date, interval)

if peak_info is not None:
    print("Most Recent Peak with MACD Level:")
    print(f"Date: {peak_info['Date']}, Price: {peak_info['Price']}, MACD: {peak_info['MACD']}")
else:
    print("No peaks found in the given data.")

print("\nMost Recent Data:")
print(f"Date: {recent['Date']}, Price: {recent['Price']}, MACD: {recent['MACD']}")

# Plot the chart with vertical line at the most recent peak
plot_chart(data, macd_line, signal_line, macd_histogram, peak_index)
