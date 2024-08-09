import pandas as pd
import os


def evaluate_short_percentage(df):
    # Ensure 'SHORT %' column is a string and strip any extra spaces
    df['SHORT %'] = df['SHORT %'].astype(str).str.strip()

    # Convert 'SHORT %' to numeric by removing non-numeric characters
    df['SHORT %'] = df['SHORT %'].replace({'N/A': None, '%': ''}, regex=True).astype(float)

    # Apply evaluation logic
    df['Evaluation'] = df['SHORT %'].apply(lambda x: (x - 50) if pd.notnull(x) else None)

    return df


def evaluate_macd_price_correlation(df):
    # Ensure required columns are in numeric format
    df['LAST PEAK PRICE'] = pd.to_numeric(df['LAST PEAK PRICE'], errors='coerce')
    df['RECENT PRICE'] = pd.to_numeric(df['RECENT PRICE'], errors='coerce')
    df['LAST PEAK MACD'] = pd.to_numeric(df['LAST PEAK MACD'], errors='coerce')
    df['RECENT MACD'] = pd.to_numeric(df['RECENT MACD'], errors='coerce')

    # Define scoring ranges based on intervals
    interval_scoring = {
        '15m': (-8, 8),
        '60m': (-10, 10),
        '90m': (-12, 12)
    }

    # Define customizable thresholds for each ticker
    # Values here are in terms of percentage for price and absolute for MACD changes
    thresholds = {
        'USDCAD': {'price': {'15m': 0.001, '60m': 0.002, '90m': 0.003},
                   'macd': {'15m': 0.1, '60m': 0.2, '90m': 0.3}},
        'AUDUSD': {'price': {'15m': 0.0015, '60m': 0.0025, '90m': 0.0035},
                   'macd': {'15m': 0.08, '60m': 0.18, '90m': 0.28}},
        'GBPUSD': {'price': {'15m': 0.002, '60m': 0.003, '90m': 0.004},
                   'macd': {'15m': 0.09, '60m': 0.19, '90m': 0.29}},
        'EURUSD': {'price': {'15m': 0.0012, '60m': 0.0022, '90m': 0.0032},
                   'macd': {'15m': 0.07, '60m': 0.17, '90m': 0.27}},
        'USDJPY': {'price': {'15m': 0.001, '60m': 0.002, '90m': 0.003},
                   'macd': {'15m': 0.05, '60m': 0.15, '90m': 0.25}}
    }

    def evaluate(row):
        if pd.isna(row['LAST PEAK PRICE']) or pd.isna(row['RECENT PRICE']) or pd.isna(row['LAST PEAK MACD']) or pd.isna(
                row['RECENT MACD']):
            return None

        # Calculate price and MACD differences
        price_diff = row['RECENT PRICE'] - row['LAST PEAK PRICE']
        macd_diff = row['RECENT MACD'] - row['LAST PEAK MACD']

        # Determine evaluation points based on price and MACD movements
        interval = row.get('Interval', '15m')
        ticker = row.get('Ticker', 'USDJPY')

        # Retrieve thresholds for the current ticker and interval
        ticker_thresholds = thresholds.get(ticker, {})
        price_threshold = ticker_thresholds.get('price', {}).get(interval, 0.001)
        macd_threshold = ticker_thresholds.get('macd', {}).get(interval, 0.1)

        min_points, max_points = interval_scoring.get(interval, (0, 0))

        # Calculate relative price change
        price_change_percentage = price_diff / row['LAST PEAK PRICE']

        # Determine the direction of movement
        price_direction = 1 if price_diff > 0 else -1
        macd_direction = 1 if macd_diff > 0 else -1

        # Evaluate price movement significance
        if abs(price_change_percentage) < price_threshold:
            price_score = 0  # Price change is insignificant
        elif price_diff > 0:
            price_score = max_points if price_change_percentage > price_threshold * 2 else max_points // 2
        else:
            price_score = min_points if price_change_percentage < -price_threshold * 2 else min_points // 2

        # Evaluate MACD movement significance
        if abs(macd_diff) < macd_threshold:
            macd_score = 0  # MACD change is insignificant
        elif macd_diff > 0:
            macd_score = max_points if macd_diff > macd_threshold * 2 else max_points // 2
        else:
            macd_score = min_points if macd_diff < -macd_threshold * 2 else min_points // 2

        # Combine price and MACD scores
        if price_direction == macd_direction:
            # Price and MACD move in the same direction, confirm trend
            total_score = (price_score + macd_score) // 2  # Minimal points if aligned
        else:
            # Price and MACD move in opposite directions
            total_score = price_score + macd_score

        return total_score

    df['MACD-Price Evaluation'] = df.apply(evaluate, axis=1)

    return df


def read_most_recent_csv(directory):
    # List all files in the directory
    files = [f for f in os.listdir(directory) if f.endswith('.csv')]

    if not files:
        raise FileNotFoundError("No CSV files found in the directory.")

    # Get full paths for all CSV files
    file_paths = [os.path.join(directory, f) for f in files]

    # Find the most recent file based on modification time
    most_recent_file = max(file_paths, key=os.path.getmtime)

    # Read the most recent file into a DataFrame
    df = pd.read_csv(most_recent_file)

    return df


# Define the directory containing the CSV files
directory = r"C:\Users\2001s\PycharmProjects\Jak poznać ślicznotkę życia\csvs"

# Read the most recent CSV file
recent_df = read_most_recent_csv(directory)

# Evaluate the SHORT % column
evaluated_df = evaluate_short_percentage(recent_df)

# Evaluate MACD and Price correlation
evaluated_df = evaluate_macd_price_correlation(evaluated_df)

# Print the evaluated DataFrame

# Set display options for Pandas DataFrame to show full content (optional)
pd.set_option('display.max_columns', None)  # Show all columns
pd.set_option('display.width', 1000)  # Set the display width to 1000 characters for full content
pd.set_option('display.max_colwidth', None)  # No truncation of column content

print(evaluated_df)