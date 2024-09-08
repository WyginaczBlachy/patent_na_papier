import yfinance as yf
from scipy.signal import find_peaks
from datetime import datetime, timedelta
import mplfinance as mpf

def get_price_peak_and_macd(ticker, start_date, end_date, interval):
    prominence_dict = {
        "USDJPY=X": 0.2,
        "EURUSD=X": 0.0002,
        "GBPUSD=X": 0.0007,
        "AUDUSD=X": 0.0007,
        "USDCAD=X": 0.0003,
        "USDPLN=X": 0.003
    }

    prominence = prominence_dict.get(ticker)

    data = yf.download(ticker, start=start_date, end=end_date, interval=interval)

    close_prices = data['Close']

    ema_12 = close_prices.ewm(span=12, adjust=False).mean()
    ema_26 = close_prices.ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_histogram = macd_line - signal_line

    peaks, _ = find_peaks(close_prices, prominence=prominence, distance=16)

    if len(peaks) >= 4:
        recent_peaks = peaks[-4:]
    elif len(peaks) > 0:
        recent_peaks = peaks[-len(peaks):]
    else:
        return None, None, data, macd_line, signal_line, macd_histogram, []

    peak_infos = []
    for peak in recent_peaks:
        peak_infos.append({
            'Date': data.index[peak],
            'Price': f"{close_prices.iloc[peak]:.4f}",
            'MACD': f"{macd_histogram.iloc[peak]:.4f}"
        })

    most_recent = {
        'Date': data.index[-1],
        'Price': f"{close_prices.iloc[-1]:.4f}",
        'MACD': f"{macd_histogram.iloc[-1]:.4f}"
    }

    return peak_infos, most_recent, data, macd_line, signal_line, macd_histogram, recent_peaks

def plot_chart(data, macd_line, signal_line, macd_histogram, peaks):
    macd_addplot = [
        mpf.make_addplot(macd_line, panel=1, color='blue', secondary_y=False, label='MACD Line'),
        mpf.make_addplot(signal_line, panel=1, color='orange', secondary_y=False, label='Signal Line'),
        mpf.make_addplot(macd_histogram, panel=1, type='bar', color='dimgray', secondary_y=True, label='Histogram')
    ]

    peak_dates = [data.index[peak] for peak in peaks] if peaks is not None else []

    mpf.plot(
        data,
        type='candle',
        style='yahoo',
        title='Candlestick Chart with MACD (Last 10 Days)',
        ylabel='Exchange Rate',
        volume=True,
        mav=(12, 26),
        figratio=(14, 7),
        datetime_format='%b %d, %H:%M',
        xrotation=45,
        addplot=macd_addplot,
        vlines=dict(
            vlines=peak_dates,
            linewidths=1,
            colors='red',
            alpha=0.7
        )
    )

ticker = "GBPUSD=X"
start_date = (datetime.now() - timedelta(days=2.1)).strftime('%Y-%m-%d')
end_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
interval = "15m"

peak_infos, recent, data, macd_line, signal_line, macd_histogram, peak_indices = get_price_peak_and_macd(ticker, start_date, end_date, interval)

if peak_infos is not None:
    print("Most Recent Peaks with MACD Levels:")
    for peak_info in peak_infos:
        print(f"Date: {peak_info['Date']}, Price: {peak_info['Price']}, MACD: {peak_info['MACD']}")
else:
    print("No peaks found in the given data.")

print("\nMost Recent Data:")
print(f"Date: {recent['Date']}, Price: {recent['Price']}, MACD: {recent['MACD']}")

plot_chart(data, macd_line, signal_line, macd_histogram, peak_indices)
