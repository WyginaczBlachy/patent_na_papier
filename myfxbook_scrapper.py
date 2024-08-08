import requests
from bs4 import BeautifulSoup


def get_short_percentage(ticker):
    url = f'https://www.myfxbook.com/community/outlook/{ticker}'

    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code != 200:
        print(f"Failed to retrieve data for ticker {ticker}, Status Code: {response.status_code}")
        return None

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all rows in the table that might contain data
    rows = soup.find_all('tr')

    # Prepare list to store short data
    short_data = []

    # Iterate over each row and extract relevant data
    for row in rows:
        cols = row.find_all('td')
        # Ensure there are columns and check if the text matches "Short"
        if len(cols) > 1 and cols[0].text.strip() == 'Short':
            percentage_text = cols[1].text.strip()  # Second column is the percentage
            # Convert percentage to decimal
            percentage_value = float(percentage_text.replace('%', '').strip()) / 100
            short_data.append(percentage_value)

    return short_data


def main():
    ticker = 'AUDUSD'  # Example ticker symbol
    short_data = get_short_percentage(ticker)

    if short_data:
        print(f"{ticker}:")
        for value in short_data:
            print(value)


if __name__ == "__main__":
    main()
