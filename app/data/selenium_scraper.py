import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from app.models import Product, Market, Price, Region  # Added Region import
from app.extensions import db
import time

logger = logging.getLogger(__name__)

class AMISSeleniumScraper:
    BASE_URL = "https://kamis.kilimo.go.ke/site/market?product=1&per_page=3000"
    WAIT_TIMEOUT = 20  # Increased timeout for slow loading

    def __init__(self, headless=True):
        self.options = webdriver.ChromeOptions()
        if headless:
            self.options.add_argument("--headless=new")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--window-size=1920,1080")
        self.service = Service(ChromeDriverManager().install())

    def scrape(self):
        driver = None
        try:
            driver = webdriver.Chrome(service=self.service, options=self.options)
            driver.get(self.BASE_URL)
            
            # Wait for dynamic content to load
            WebDriverWait(driver, self.WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.table"))
            )
            
            # Additional wait for JavaScript rendering
            time.sleep(2)
            
            # Extract data using your working approach
            html = driver.page_source
            prices = self._parse_html(html)
            
            # Save to database
            return self._save_to_db(prices)
            
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}", exc_info=True)
            return False
        finally:
            if driver:
                driver.quit()

    def _parse_html(self, html):
        """Parse the HTML you successfully scraped before"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find("table", {"class": "table"})
        prices = []
        
        if not table:
            logger.error("Table not found in HTML")
            return prices
            
        for row in table.find_all("tr"):
            cols = row.find_all("td")
            # Based on AMIS Kenya's structure
            if len(cols) >= 10:
                # Extract the county (which will be saved as region)
                # The county column is at index 3 in the AMIS Kenya table
                county_name = cols[3].text.strip()
                market_name = cols[4].text.strip()
                
                # Use county as the region name, with a fallback if empty
                region_name = county_name if county_name else "Unknown County"
                
                prices.append({
                    "commodity": cols[0].text.strip(),
                    "market": market_name,
                    "region": region_name,  # Use county as region
                    "wholesale": self._parse_price(cols[5].text),
                    "retail": self._parse_price(cols[6].text),
                    "date": datetime.strptime(cols[9].text.strip(), "%Y-%m-%d").date()
                })
        return prices

    def _parse_price(self, price_str):
        """Convert price strings like 'KSh 50.00/kg' to float"""
        try:
            return float(price_str.replace("KSh", "").split("/")[0].strip())
        except (ValueError, AttributeError):
            return None

    def _save_to_db(self, prices):
        saved_count = 0
        for item in prices:
            try:
                # Check for empty region name and provide a default if needed
                region_name = item["region"] if item["region"] else "Unknown County"
                
                # Get or create Region
                region = Region.query.filter_by(name=region_name).first()
                if not region:
                    region = Region(name=region_name)
                    db.session.add(region)
                    db.session.flush()  # Flush to get the region ID
                
                # Get or create Market with region_id
                market = Market.query.filter_by(name=item["market"]).first()
                if not market:
                    market = Market(
                        name=item["market"],
                        region_id=region.id  # Set the region_id
                    )
                    db.session.add(market)
                    db.session.flush()  # Flush to get the market ID
                elif market.region_id is None:
                    # Update existing market with region if missing
                    market.region_id = region.id
                
                # Get or create Product
                product = Product.query.filter_by(name=item["commodity"]).first()
                if not product:
                    product = Product(name=item["commodity"])
                    db.session.add(product)
                    db.session.flush()  # Flush to get the product ID
                
                # Create Price record
                db.session.add(Price(
                    product=product,
                    market=market,
                    wholesale_price=item["wholesale"],
                    retail_price=item["retail"],
                    date=item["date"],
                    source="AMIS Kenya (Selenium)"
                ))
                saved_count += 1
            except Exception as e:
                logger.error(f"Failed to save price record: {str(e)}")
                db.session.rollback()
        
        try:
            db.session.commit()
            logger.info(f"Saved {saved_count} new price records")
            return saved_count
        except Exception as e:
            logger.error(f"Failed to commit changes: {str(e)}")
            db.session.rollback()
            return 0