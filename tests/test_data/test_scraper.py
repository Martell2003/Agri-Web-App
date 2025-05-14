import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from agri_price_tracker.app.data.scraper import AMISKenyaScraper
scraper = AMISKenyaScraper()
test_data = scraper.scrape_price_data()
print(test_data[:2])  # Should show first 2 records without errors