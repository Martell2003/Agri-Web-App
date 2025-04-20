import requests
from app.extensions import db
from app.models.price import Price
from app.models.product import Product
from app.models.market import Market
from datetime import datetime

def fetch_prices(api_url, api_key=None):
    """
    Fetch agricultural price data from an API (e.g., FAO FAOSTAT).
    :param api_url: The API endpoint URL.
    :param api_key: Optional API key (not needed for FAOSTAT).
    :return: List of Price objects.
    """
    headers = {
        "User-Agent": "AgriPriceTracker/1.0"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        prices = []
        # FAOSTAT response structure: data is in 'data' key
        for entry in data.get('data', []):
            product_name = entry.get('item_name', 'Unknown Product')
            price_value = float(entry.get('value', 0.0))  # Producer price in USD/tonne
            year = int(entry.get('year', datetime.now().year))
            timestamp = datetime(year, 1, 1)  # Default to Jan 1 of the year
            market_name = 'National Average'  # FAOSTAT doesn’t specify markets

            # Fetch or create Product and Market
            product = Product.query.filter_by(name=product_name).first()
            if not product:
                product = Product(name=product_name)
                db.session.add(product)

            market = Market.query.filter_by(name=market_name).first()
            if not market:
                market = Market(name=market_name, region_id=1)
                db.session.add(market)

            # Flush to assign IDs
            db.session.flush()

            price = Price(
                product_id=product.id,
                market_id=market.id,
                price=price_value,
                timestamp=timestamp
            )
            prices.append(price)
        
        db.session.add_all(prices)
        db.session.commit()
        print(f"Fetched and saved {len(prices)} price entries from API.")
        return prices

    except requests.RequestException as e:
        print(f"Error fetching from API: {e}")
        return []
    except ValueError as e:
        print(f"Data parsing error: {e}")
        return []

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        # Test with FAO FAOSTAT for maize in Kenya (2023)
        test_url = "http://fenixservices.fao.org/faostat/api/v1/en/data/PP?area=114&item=15&element=5532&year=2023&format=json"
        fetch_prices(test_url)