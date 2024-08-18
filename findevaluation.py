import os
from evaluation import evaluate_short_percentage, evaluate_macd_price_correlation
import pandas as pd
from datetime import datetime
import schedule
import time

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

def job():

    directory = r"C:\Users\2001s\PycharmProjects\Jak poznać ślicznotkę życia\csvs"

    # Read the most recent CSV file
    recent_df = read_most_recent_csv(directory)

    # Evaluate the SHORT % column
    evaluated_df = evaluate_short_percentage(recent_df)

    # Evaluate MACD and Price correlation
    evaluated_df = evaluate_macd_price_correlation(evaluated_df)
    evaluated_df['EVALUATION'] = evaluated_df['Evaluation'] + evaluated_df['MACD-Price Evaluation']
    #evaluated_df = evaluated_df.drop(['Evaluation', 'MACD-Price Evaluation'], axis=1)
    print(evaluated_df)

    # Check if any value in 'EVALUATION' is greater than or equal to 30 in absolute terms
    if (abs(evaluated_df['EVALUATION']) >= 40).any():
        output_dir = r"C:\Users\2001s\PycharmProjects\Jak poznać ślicznotkę życia\evals"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f"signals_{timestamp}.csv"
        csv_file_path = os.path.join(output_dir, csv_filename)
        evaluated_df.to_csv(csv_file_path, index=False)

job()

# Schedule the job to run every 15 minutes
schedule.every(15).minutes.do(job)

# Keep the script running to allow the scheduled job to execute
while True:
    schedule.run_pending()
    time.sleep(1)  # Sleep for a short time to prevent high CPU usage