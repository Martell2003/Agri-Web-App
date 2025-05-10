import schedule
import time
import logging
from app.data.scraper import scrape_indexmundi_maize
from app.data.processor import process_price_data

logger = logging.getLogger(__name__)

def run_scraper():
    """Run the scraper and process data."""
    logger.info("Starting scheduled scraper run")
    price_data = scrape_indexmundi_maize()
    new_prices = process_price_data(price_data)
    logger.info(f"Scheduled scraper run completed, saved {new_prices} new prices")

def start_scheduler():
    """Schedule the scraper to run daily at 2 AM."""
    schedule.every().day.at("02:00").do(run_scraper)
    logger.info("Scheduler started, waiting for tasks")
    while True:
        schedule.run_pending()
        time.sleep(60)