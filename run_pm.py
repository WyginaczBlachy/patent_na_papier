
import schedule
import time
from portfolio_manager import update_portfolio

update_portfolio()
schedule.every(2).minutes.do(update_portfolio)

while True:
    schedule.run_pending()
    time.sleep(1)