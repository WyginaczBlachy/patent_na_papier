import os
import glob
import pandas as pd
from datetime import datetime
import yfinance as yf
import requests

initial_portfolio_value = 500.0
starting_investment_per_ticker = 100.0

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
def send_telegram_message(message):
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(TELEGRAM_API_URL, data=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}")

def fetch_current_price(ticker):
    yahoo_ticker = f"{ticker}=X"
    try:
        stock = yf.Ticker(yahoo_ticker)
        latest_price = stock.history(period="1d").tail(1)['Close'].iloc[0]
        return latest_price
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

def update_portfolio():
    eval_directory = r"C:\Users\2001s\PycharmProjects\Jak poznać ślicznotkę życia\evals"
    portfolio_directory = r"C:\Users\2001s\PycharmProjects\Jak poznać ślicznotkę życia\portfel"
    history_directory = r"C:\Users\2001s\PycharmProjects\Jak poznać ślicznotkę życia\history"

    csv_files = glob.glob(os.path.join(eval_directory, 'signals_*.csv'))
    latest_csv = max(csv_files, key=os.path.getmtime)
    df = pd.read_csv(latest_csv)

    results = {}

    for _, row in df.iterrows():
        ticker = row['Ticker']
        if ticker not in results:
            results[ticker] = {
                'Evaluation': row['Evaluation'],
                'MACD-Price Evaluation Sum': 0.0,
                'Transaction Price': None
            }
        results[ticker]['MACD-Price Evaluation Sum'] += row['MACD-Price Evaluation']

        if row['Interval'] == '15m':
            if results[ticker]['Transaction Price'] is None:
                results[ticker]['Transaction Price'] = row['RECENT PRICE']

    results_df = pd.DataFrame(results).T.reset_index()
    results_df.columns = ['Ticker', 'Evaluation', 'MACD-Price Evaluation Sum', 'Transaction Price']
    results_df['Total Evaluation'] = results_df['Evaluation'] + results_df['MACD-Price Evaluation Sum']

    portfolio_file = os.path.join(portfolio_directory, 'portfolio.csv')
    if os.path.exists(portfolio_file):
        portfolio_df = pd.read_csv(portfolio_file)
    else:
        portfolio_df = pd.DataFrame(columns=['Timestamp', 'Ticker', 'Transaction Date', 'Transaction Price',
                                             'Investment Amount', 'Position', 'Current Price', 'Profit/Loss',
                                             'Monetary Gain/Loss', 'Take Profit', 'Stop Loss', 'Min Profit/Loss',
                                             'Max Profit/Loss'
                                             ])
        portfolio_df['Take Profit'] = 0.27
        portfolio_df['Stop Loss'] = -0.23
        portfolio_df['Min Profit/Loss'] = 0.0
        portfolio_df['Max Profit/Loss'] = 0.0

    history_file = os.path.join(history_directory, 'transaction_history.csv')
    if os.path.exists(history_file):
        history_df = pd.read_csv(history_file)
    else:
        history_df = pd.DataFrame(columns=['Transaction Date', 'Close Date', 'Ticker', 'Transaction Price',
                                           'Investment Amount', 'Position', 'Current Price', 'Profit/Loss',
                                           'Monetary Gain/Loss', 'Min Profit/Loss', 'Max Profit/Loss', 'Action'
                                           ])

    print("Fetching current prices...")
    for ticker in portfolio_df['Ticker'].unique():
        print(f"Fetching price for ticker: {ticker}")
        current_price = fetch_current_price(ticker)
        if current_price is not None:
            portfolio_df.loc[portfolio_df['Ticker'] == ticker, 'Current Price'] = current_price
            print(f"Updated {ticker} price to {current_price}")
        else:
            print(f"Failed to fetch price for {ticker}")

    def calculate_profit_loss(row):
        if row['Position'] == 'Long':
            return (row['Current Price'] - row['Transaction Price']) / row['Transaction Price'] * 100
        elif row['Position'] == 'Short':
            return (row['Transaction Price'] - row['Current Price']) / row['Transaction Price'] * 100
        return 0

    def calculate_monetary_gain_loss(row):
        leverage = 30
        gain_loss = row['Investment Amount'] * row['Profit/Loss'] * leverage / 100
        return gain_loss

    def update_min_max(row):
        new_min = min(row['Min Profit/Loss'], row['Profit/Loss'])
        new_max = max(row['Max Profit/Loss'], row['Profit/Loss'])

        return pd.Series([new_min, new_max])
    result = portfolio_df.apply(update_min_max, axis=1)

    if len(portfolio_df) > 0:
        portfolio_df.iloc[:, portfolio_df.columns.get_loc('Min Profit/Loss')] = result[0]
        portfolio_df.iloc[:, portfolio_df.columns.get_loc('Max Profit/Loss')] = result[1]

    portfolio_df['Profit/Loss'] = portfolio_df.apply(calculate_profit_loss, axis=1)
    portfolio_df['Monetary Gain/Loss'] = portfolio_df.apply(calculate_monetary_gain_loss, axis=1)

    portfolio_df['Stop Loss'] = -0.23 + portfolio_df['Max Profit/Loss']
    portfolio_df['Take Profit'] = 0.27 + portfolio_df['Min Profit/Loss']

    current_positions_value = portfolio_df['Monetary Gain/Loss'].sum()
    total_history_value = history_df['Monetary Gain/Loss'].sum() if not history_df.empty else 0.0
    total_portfolio_value = initial_portfolio_value + current_positions_value + total_history_value

    available_capital = total_portfolio_value - portfolio_df['Investment Amount'].sum()

    new_positions = []
    for _, row in results_df.iterrows():
        ticker_in_portfolio = portfolio_df[portfolio_df['Ticker'] == row['Ticker']]
        if ticker_in_portfolio.empty:
            if row['Total Evaluation'] > 50 and available_capital >= starting_investment_per_ticker:
                new_positions.append({
                    'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Transaction Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Ticker': row['Ticker'],
                    'Transaction Price': row['Transaction Price'],
                    'Investment Amount': starting_investment_per_ticker,
                    'Position': 'Long',
                    'Current Price': row['Transaction Price'],
                    'Profit/Loss': 0,
                    'Monetary Gain/Loss': 0,
                    'Take Profit': 0.27,
                    'Stop Loss': -0.23,
                    'Min Profit/Loss': 0.0,
                    'Max Profit/Loss': 0.0
                })
                send_telegram_message(f"Position opened: {row['Ticker']} - Long at ${row['Transaction Price']:.5f}")
                available_capital -= starting_investment_per_ticker
            elif row['Total Evaluation'] < -50 and available_capital >= starting_investment_per_ticker:
                new_positions.append({
                    'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Transaction Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Ticker': row['Ticker'],
                    'Transaction Price': row['Transaction Price'],
                    'Investment Amount': starting_investment_per_ticker,
                    'Position': 'Short',
                    'Current Price': row['Transaction Price'],
                    'Profit/Loss': 0,
                    'Monetary Gain/Loss': 0,
                    'Take Profit': 0.27,
                    'Stop Loss': -0.23,
                    'Min Profit/Loss': 0.0,
                    'Max Profit/Loss': 0.0
                })
                send_telegram_message(f"Position opened: {row['Ticker']} - Short at ${row['Transaction Price']:.5f}")
                available_capital -= starting_investment_per_ticker

    if new_positions:
        new_positions_df = pd.DataFrame(new_positions)
        if not new_positions_df.empty and not new_positions_df.isna().all(axis=1).all():
            portfolio_df = pd.concat([portfolio_df, new_positions_df], ignore_index=True)

    to_remove = []
    history_entries = []
    for index, row in portfolio_df.iterrows():
        if row['Position'] == 'Long':
            if row['Profit/Loss'] >= row['Take Profit']:
                evaluation_for_ticker = results_df[results_df['Ticker'] == row['Ticker']]['Total Evaluation'].values[0]
                if evaluation_for_ticker <= 50:
                    action = 'Closed (Take Profit)'
                else:
                    continue
            elif row['Profit/Loss'] <= row['Stop Loss']:
                action = 'Closed (Stop Loss)'
            else:
                continue
        elif row['Position'] == 'Short':
            if row['Profit/Loss'] >= row['Take Profit']:
                evaluation_for_ticker = results_df[results_df['Ticker'] == row['Ticker']]['Total Evaluation'].values[0]
                if evaluation_for_ticker >= -50:
                    action = 'Closed (Take Profit)'
                else:
                    continue
            elif row['Profit/Loss'] <= row['Stop Loss']:
                action = 'Closed (Stop Loss)'
            else:
                continue

        history_entries.append({
            'Transaction Date': row['Transaction Date'],
            'Close Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Ticker': row['Ticker'],
            'Open @ Price': row['Transaction Price'],
            'Investment Amount': row['Investment Amount'],
            'Position': row['Position'],
            'Closed @ Price': row['Current Price'],
            'Profit/Loss': row['Profit/Loss'],
            'Monetary Gain/Loss': row['Monetary Gain/Loss'],
            'Min Profit/Loss': row['Min Profit/Loss'],
            'Max Profit/Loss': row['Max Profit/Loss'],
            'Action': action
        })
        send_telegram_message(f"Position closed: {row['Ticker']} - {row['Position']} at ${row['Current Price']:.5f} {action}")
        to_remove.append(index)

    portfolio_df = portfolio_df.drop(to_remove)

    if history_entries:
        history_entries_df = pd.DataFrame(history_entries)
        history_df = pd.concat([history_df, history_entries_df], ignore_index=True)

    portfolio_df.to_csv(portfolio_file, index=False)
    history_df.to_csv(history_file, index=False)

    print("Results DataFrame:")
    print(results_df)
    print("Portfolio DataFrame:")
    print(portfolio_df)
    print(f"Current Portfolio Value: ${total_portfolio_value:.2f}")
    print("Transaction History DataFrame:")
    print(history_df.tail())

