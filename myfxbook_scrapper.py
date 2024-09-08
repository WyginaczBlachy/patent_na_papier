import requests
from bs4 import BeautifulSoup


def get_short_percentage(ticker):
    url = f'https://www.myfxbook.com/community/outlook/{ticker}'

    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to retrieve data for ticker {ticker}, Status Code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    rows = soup.find_all('tr')

    short_data = []

    for row in rows:
        cols = row.find_all('td')
        if len(cols) > 1 and cols[0].text.strip() == 'Short':
            percentage_text = cols[1].text.strip()
            percentage_value = float(percentage_text.replace('%', '').strip()) / 100
            short_data.append(percentage_value)

    return short_data

