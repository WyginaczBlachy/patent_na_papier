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

    def evaluate(row):
        if pd.isna(row['LAST PEAK PRICE']) or pd.isna(row['RECENT PRICE']) or pd.isna(row['LAST PEAK MACD']) or pd.isna(
                row['RECENT MACD']):
            return None

        # Price and MACD differences
        price_diff = row['RECENT PRICE'] - row['LAST PEAK PRICE']
        macd_diff = row['RECENT MACD'] - row['LAST PEAK MACD']

        # Determine evaluation points based on price and MACD movements
        interval = row.get('Interval', '15m')
        min_points, max_points = interval_scoring.get(interval, (0, 0))

        if price_diff == 0:
            if macd_diff < 0:
                return min_points  # Price stable, MACD falling (bearish)
            elif macd_diff > 0:
                return max_points  # Price stable, MACD rising (bullish)
            else:
                return 0  # Both stable
        elif price_diff > 0:
            if macd_diff < 0:
                return min_points  # Price rising, MACD falling (bearish)
            elif macd_diff > 0:
                return max_points  # Price rising, MACD rising (bullish)
            else:
                return min_points // 2  # Price rising, MACD stable (slightly bullish)
        else:  # price_diff < 0
            if macd_diff < 0:
                return max_points // 2  # Price falling, MACD falling (slightly bullish)
            elif macd_diff > 0:
                return min_points  # Price falling, MACD rising (bearish)
            else:
                return 0  # Price falling, MACD stable (neutral)

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