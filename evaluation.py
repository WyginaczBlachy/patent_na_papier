import pandas as pd

def evaluate_short_percentage(df):
    df['SHORT %'] = df['SHORT %'].astype(str).str.strip()

    df['SHORT %'] = df['SHORT %'].replace({'N/A': None, '%': ''}, regex=True).astype(float)

    df['Evaluation'] = df['SHORT %'].apply(lambda x: (x - 50) if pd.notnull(x) else None)

    return df


def evaluate_macd_price_correlation(df):
    df['LAST PEAK PRICE'] = pd.to_numeric(df['LAST PEAK PRICE'], errors='coerce')
    df['RECENT PRICE'] = pd.to_numeric(df['RECENT PRICE'], errors='coerce')
    df['LAST PEAK MACD'] = pd.to_numeric(df['LAST PEAK MACD'], errors='coerce')
    df['RECENT MACD'] = pd.to_numeric(df['RECENT MACD'], errors='coerce')

    interval_scoring = {
        '15m': (-10, 10),
        '60m': (-14, 14),
        '90m': (-11, 11)
    }


    thresholds = {
        'USDCAD': {'price': {'15m': 0.0008, '60m': 0.0022, '90m': 0.0026},
                   'macd': {'15m': 0.00012, '60m': 0.00019, '90m': 0.0003}},
        'AUDUSD': {'price': {'15m': 0.002, '60m': 0.0024, '90m': 0.0026},
                   'macd': {'15m': 0.0001, '60m': 0.00022, '90m': 0.00025}},
        'GBPUSD': {'price': {'15m': 0.002, '60m': 0.002, '90m': 0.0023},
                   'macd': {'15m': 0.0002, '60m': 0.00027, '90m': 0.0003}},
        'EURUSD': {'price': {'15m': 0.001, '60m': 0.0023, '90m': 0.003},
                   'macd': {'15m': 0.00006, '60m': 0.00025, '90m': 0.0003}},
        'USDJPY': {'price': {'15m': 0.002, '60m': 0.004, '90m': 0.006},
                   'macd': {'15m': 0.03, '60m': 0.085, '90m': 0.11}},
        'USDPLN': {'price': {'15m': 0.0007, '60m': 0.003, '90m': 0.006},
                   'macd': {'15m': 0.00040, '60m': 0.0007, '90m': 0.00082}},
                   }

    def evaluate(row):
        if pd.isna(row['LAST PEAK PRICE']) or pd.isna(row['RECENT PRICE']) or pd.isna(row['LAST PEAK MACD']) or pd.isna(
                row['RECENT MACD']):
            return None

        price_diff = row['RECENT PRICE'] - row['LAST PEAK PRICE']
        macd_diff = row['RECENT MACD'] - row['LAST PEAK MACD']
        if row['RECENT MACD'] <= 0:
            if row['RECENT MACD'] <= row['LAST PEAK MACD']:
                macd_movement = -1
            else:
                macd_movement = 1
        else:
            if row['RECENT MACD'] > row['LAST PEAK MACD']:
                macd_movement = 1
            else:
                macd_movement = -1
        if row['LAST PEAK PRICE'] != 0:
            price_percentage_change = (price_diff / row['LAST PEAK PRICE']) * 100
        else:
            price_percentage_change = 0

        abs_macd_diff = abs(macd_diff)

        interval = row.get('Interval', '15m')
        ticker = row.get('Ticker', 'USDJPY')

        ticker_thresholds = thresholds.get(ticker, {})
        price_threshold = ticker_thresholds.get('price', {}).get(interval, 0.0001)
        macd_threshold = ticker_thresholds.get('macd', {}).get(interval, 0.1)

        min_points, max_points = interval_scoring.get(interval, (0, 0))

        if price_threshold > 0:
            price_checkpoints = abs(price_percentage_change) // (price_threshold * 100)
        else:
            price_checkpoints = 0

        if macd_threshold > 0:
            macd_checkpoints = abs_macd_diff // macd_threshold
        else:
            macd_checkpoints = 0

        if price_percentage_change > 0:
            price_score = price_checkpoints * min_points
        else:
            price_score = price_checkpoints * max_points

        if macd_movement > 0:
            macd_score = macd_checkpoints * max_points
        else:
            macd_score = macd_checkpoints * min_points

        total_score = price_score + macd_score

        return total_score

    df['MACD-Price Evaluation'] = df.apply(evaluate, axis=1)

    return df




