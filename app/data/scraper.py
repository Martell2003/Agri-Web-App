import requests
from bs4 import BeautifulSoup
import logging
import time
import random
import json
from datetime import datetime
from app.models.product import Product
from app.models.market import Market
from app.models.price import Price
from app.models.region import Region
from app.extensions import db
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AMISKenyaScraper:
    BASE_URL = "https://kamis.kilimo.go.ke/site/market?product=1&per_page=3000"
    MARKET_URL = f"{BASE_URL}/site/market"
   
    def __init__(self):
        self.base_url = "https://kamis.kilimo.go.ke/site/market?product=1&per_page=3000"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://kamis.kilimo.go.ke/site/market?product=1&per_page=3000"
        }
        self.session = requests.Session()
        self.request_delay = (1, 3)  # Random delay between requests in seconds
       
    def _make_request(self, url, method="get", params=None, data=None, retries=3):
        """Make HTTP request with retry logic and polite delays"""
        time.sleep(random.uniform(*self.request_delay))
       
        for attempt in range(retries):
            try:
                if method.lower() == "get":
                    response = self.session.get(
                        url,
                        headers=self.headers,
                        params=params,
                        timeout=15
                    )
                else:
                    response = self.session.post(
                        url,
                        headers=self.headers,
                        params=params,
                        data=data,
                        timeout=15
                    )
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt+1} failed for {url}: {str(e)}")
                if attempt == retries - 1:
                    logger.error(f"Failed to fetch {url} after {retries} attempts")
                    raise  # Re-raise the exception for handling upstream
                time.sleep(2 * (attempt + 1))  # Exponential backoff
       
        return None

    def _get_or_create_market(self, market_data):
        """Get or create Market and associated Region"""
        # First handle region - FIX: Check if region value is not None
        region = None
        region_name = market_data.get('region')
        if region_name and region_name.strip():  # Ensure region exists and is not empty
            region = Region.query.filter_by(name=region_name).first()
            if not region:
                region = Region(name=region_name)
                db.session.add(region)
                db.session.commit()
                logger.info(f"Created new region: {region_name}")
        else:
            # Use a default region name if none is provided
            default_region_name = "Unknown Region"
            region = Region.query.filter_by(name=default_region_name).first()
            if not region:
                region = Region(name=default_region_name)
                db.session.add(region)
                db.session.commit()
                logger.info(f"Created default region: {default_region_name}")
       
        # Then handle market
        market_name = market_data.get('name', 'Unknown Market').strip()
        market = Market.query.filter_by(name=market_name).first()
        if not market:
            market = Market(
                name=market_name,
                region=region,
                latitude=market_data.get('latitude'),
                longitude=market_data.get('longitude')
            )
            db.session.add(market)
            db.session.commit()
            logger.info(f"Created new market: {market_name}")
        return market

    def _get_or_create_product(self, product_data):
        """Get or create Product"""
        product_name = product_data.get('name', 'Unknown Product').strip()
        product = Product.query.filter_by(name=product_name).first()
        if not product:
            # Create product with only the fields that exist in your model
            product = Product(
                name=product_name
                # Removed category field as it doesn't exist in your model
            )
            db.session.add(product)
            db.session.commit()
            logger.info(f"Created new product: {product_name}")
        return product

    def scrape_and_save_prices(self, market_id=None, commodity_id=None, date=None):
        """
        Scrape price data and save to database
       
        Args:
            market_id: Specific market ID to filter by
            commodity_id: Specific commodity ID to filter by
            date: Date to filter by (format: YYYY-MM-DD)
           
        Returns:
            Tuple: (success_count, error_count)
        """
        try:
            raw_data = self.scrape_price_data(market_id, commodity_id, date)
            success_count = 0
            error_count = 0
           
            for item in raw_data:
                try:
                    # Prepare market data
                    market_data = {
                        'name': item.get('market', 'Unknown Market'),
                        'region': item.get('county'),  # Map county to region
                        'latitude': item.get('latitude'),
                        'longitude': item.get('longitude')
                    }
                   
                    # Prepare product data
                    product_data = {
                        'name': item.get('commodity', 'Unknown Product')
                        # Removed unit field as it's not in your Product model
                    }
                   
                    # Get or create models
                    market = self._get_or_create_market(market_data)
                    product = self._get_or_create_product(product_data)
                   
                    # Parse date (assuming item has 'date' field)
                    trade_date = None
                    try:
                        if 'date' in item and item['date']:
                            trade_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
                        else:
                            trade_date = datetime.now().date()
                    except ValueError:
                        # Handle malformed dates
                        logger.warning(f"Invalid date format: {item.get('date')}, using current date")
                        trade_date = datetime.now().date()
                   
                    # Extract and clean price values - these are the actual column names from the error log
                    wholesale_price = self._parse_price(item.get('wholesale'))
                    retail_price = self._parse_price(item.get('retail'))
                    
                    # Create price entry - split into wholesale and retail prices
                    try:
                        # Map the columns properly
                        wholesale_price = self._parse_price(item.get('wholesale'))
                        retail_price = self._parse_price(item.get('retail'))
                        
                        if wholesale_price is not None:
                            wholesale_price_entry = Price(
                                product_id=product.id,
                                market_id=market.id,
                                price=wholesale_price,
                                timestamp=datetime.now()
                            )
                            db.session.add(wholesale_price_entry)
                        
                        if retail_price is not None:
                            retail_price_entry = Price(
                                product_id=product.id,
                                market_id=market.id,
                                price=retail_price,
                                timestamp=datetime.now()
                            )
                            db.session.add(retail_price_entry)
                        
                        db.session.commit()
                        success_count += 1
                        
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"Failed to save price records: {str(e)}")
                        continue
                   
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Failed to save price record: {str(e)}")
                    logger.error(f"Item data: {json.dumps(item)}")
                    error_count += 1
                    continue
                   
            return (success_count, error_count)
           
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}")
            return (0, 0)

    def run_daily_scrape(self):
        """Run daily scrape job to be called by scheduler"""
        logger.info("Starting daily price scrape")
       
        # First update markets and products
        try:
            markets = self.get_markets()
            commodities = self.get_commodities()
            logger.info(f"Updated {len(markets)} markets and {len(commodities)} commodities")
        except Exception as e:
            logger.error(f"Failed to update markets/commodities: {str(e)}")
       
        # Then scrape and save prices
        success, errors = self.scrape_and_save_prices()
        logger.info(f"Daily scrape completed. Saved {success} records, {errors} errors")
       
        return success > 0  # Return True if any records were saved
               
    def get_markets(self):
        """Scrape available markets"""
        url = f"{self.base_url}/site/market"
        logger.info(f"Fetching markets from {url}")
       
        response = self._make_request(url)
        if not response:
            return []
           
        soup = BeautifulSoup(response.text, "html.parser")
       
        # Look for market dropdown options
        market_select = soup.find("select", {"id": "place_id"})
        if not market_select:
            logger.warning("Market dropdown not found")
            return []
           
        markets = []
        for option in market_select.find_all("option"):
            value = option.get("value")
            if value and value.strip():
                markets.append({
                    "id": value,
                    "name": option.text.strip()
                })
               
        logger.info(f"Found {len(markets)} markets")
        return markets
       
    def get_commodities(self):
        """Scrape available commodities"""
        url = f"{self.base_url}/site/market"
        logger.info(f"Fetching commodities from {url}")
       
        response = self._make_request(url)
        if not response:
            return []
           
        soup = BeautifulSoup(response.text, "html.parser")
       
        # Look for commodity dropdown options
        commodity_select = soup.find("select", {"id": "commodity_id"})
        if not commodity_select:
            logger.warning("Commodity dropdown not found")
            return []
           
        commodities = []
        for option in commodity_select.find_all("option"):
            value = option.get("value")
            if value and value.strip():
                commodities.append({
                    "id": value,
                    "name": option.text.strip()
                })
               
        logger.info(f"Found {len(commodities)} commodities")
        return commodities
       
    def scrape_price_data(self, market_id=None, commodity_id=None, date=None):
        """
        Scrape price data with optional filters
       
        Args:
            market_id: Specific market ID to filter by
            commodity_id: Specific commodity ID to filter by
            date: Date to filter by (format: YYYY-MM-DD)
           
        Returns:
            List of dictionaries containing price data
        """
        # First load the main page to get the CSRF token
        main_url = f"{self.base_url}/site/market"
        main_response = self._make_request(main_url)
        if not main_response:
            return []
           
        main_soup = BeautifulSoup(main_response.text, "html.parser")
       
        # Try to find the CSRF token
        csrf_token = None
        csrf_meta = main_soup.find("meta", {"name": "csrf-token"})
        if csrf_meta:
            csrf_token = csrf_meta.get("content")
            self.headers["X-CSRF-Token"] = csrf_token
           
        # Prepare the search parameters
        search_url = f"{self.base_url}/site/search"
        search_data = {}
       
        if market_id:
            search_data["place_id"] = market_id
        if commodity_id:
            search_data["commodity_id"] = commodity_id
        if date:
            search_data["trade_date"] = date
           
        # If we have any search filters, use them
        if search_data:
            logger.info(f"Searching with filters: {search_data}")
            search_response = self._make_request(search_url, method="post", data=search_data)
            if not search_response:
                return []
            response_text = search_response.text
        else:
            # Otherwise just use the main page
            response_text = main_response.text
           
        soup = BeautifulSoup(response_text, "html.parser")
       
        # Find the data table
        table = soup.find("table", {"class": "table"})
        if not table:
            logger.warning("Price table not found")
            return []
           
        # Extract headers
        headers = []
        header_row = table.find("thead").find("tr")
        if not header_row:
            logger.warning("Table header row not found")
            return []
            
        for th in header_row.find_all("th"):
            headers.append(th.text.strip().lower().replace(" ", "_"))
            
        # Log headers to debug
        logger.info(f"Found table headers: {headers}")
           
        # Extract price data
        price_data = []
        tbody = table.find("tbody")
        if not tbody:
            logger.warning("Table body not found")
            return []
            
        for row in tbody.find_all("tr"):
            row_data = {}
            cols = row.find_all("td")
           
            for i, col in enumerate(cols):
                if i < len(headers):
                    row_data[headers[i]] = col.text.strip()
                   
            # Add timestamp
            row_data["scraped_at"] = datetime.now().isoformat()
           
            # Try to extract coordinates (if available)
            location_link = row.find("a", {"title": "View on map"})
            if location_link and "onclick" in location_link.attrs:
                onclick = location_link["onclick"]
                # Try to extract lat/long from onclick attribute
                coords = re.search(r"showMap\(([^,]+),\s*([^)]+)\)", onclick)
                if coords:
                    row_data["latitude"] = coords.group(1).strip()
                    row_data["longitude"] = coords.group(2).strip()
           
            # Clean numeric values
            for key in ["wholesale_price", "retail_price", "supply"]:
                if key in row_data:
                    row_data[key] = self._parse_price(row_data[key])
            
            # Debug logging for first record
            if len(price_data) == 0:
                logger.info(f"Sample row data: {json.dumps(row_data)}")
                       
            price_data.append(row_data)
           
        logger.info(f"Scraped {len(price_data)} price records")
        return price_data

    def _parse_price(self, price_str):
        """Helper to convert price strings like '41.11/Kg' to float"""
        if not price_str or not isinstance(price_str, str) or price_str.strip() == "-":
            return None
        try:
            # Extract numeric part before slash
            numeric_part = price_str.split("/")[0].strip()
            # Remove non-numeric characters except decimal point
            clean_value = ''.join(c for c in numeric_part if c.isdigit() or c == '.')
            return float(clean_value) if clean_value else None
        except (ValueError, AttributeError):
            return None
       
# Example usage
if __name__ == "__main__":
    scraper = AMISKenyaScraper()
   
    # Option 1: Get all price data
    all_prices = scraper.scrape_price_data()
    print(f"Retrieved {len(all_prices)} price records")
   
    # Option 2: Get markets and commodities first (useful for UI dropdown options)
    markets = scraper.get_markets()
    commodities = scraper.get_commodities()
    print(f"Found {len(markets)} markets and {len(commodities)} commodities")
   
    # Option 3: Run complete scrape
    # success, errors = scraper.scrape_and_save_prices()
    # print(f"Complete scrape retrieved {success} records with {errors} errors")
   
    # Print sample of the data
    if all_prices:
        print("\nSample data:")
        for price in all_prices[:3]:
            print(json.dumps(price, indent=2))