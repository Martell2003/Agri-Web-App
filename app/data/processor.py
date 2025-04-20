from ..models import Price, db
from datetime import datetime

def save_prices(prices, market_id):
    """
    Save scraped or fetched prices to the database.
    """
    try:
        for item in prices:
            price = Price(
                product=item['product'],
                price=float(item['price']),
                market_id=market_id,
                timestamp=datetime.utcnow()
            )
            db.session.add(price)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error saving prices to database: {e}")
        db.session.rollback()
        return False
    
    #data handling and storage
    
import pandas as pd
from ..models import Price, db
from datetime import datetime

def clean_and_process_data(prices):
    """
    Clean and process the scraped or fetched data.
    """
    try:
        # Convert the data to a Pandas DataFrame
        df = pd.DataFrame(prices)

        # Example cleaning steps:
        # 1. Remove rows with missing prices
        df = df.dropna(subset=['price'])
        # 2. Convert price to numeric (remove currency symbols, etc.)
        df['price'] = df['price'].replace('[\$,]', '', regex=True).astype(float)
        # 3. Standardize product names (e.g., convert to lowercase)
        df['product'] = df['product'].str.lower().str.strip()

        return df.to_dict('records')
    except Exception as e:
        print(f"Error cleaning and processing data: {e}")
        return []

def save_prices(prices, market_id):
    """
    Save cleaned and processed prices to the database.
    """
    try:
        # Clean and process the data
        cleaned_prices = clean_and_process_data(prices)

        # Save each price to the database
        for item in cleaned_prices:
            price = Price(
                product=item['product'],
                price=item['price'],
                market_id=market_id,
                timestamp=datetime.utcnow()
            )
            db.session.add(price)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error saving prices to database: {e}")
        db.session.rollback()
        return False
    
    #function to calculate avaerage prices

from sqlalchemy import func
from ..models import price

def calculate_average_prices(market_id):

    """
    Calculate average prices for each product in a market.
    """

    try:
        avg_prices = db.session.query(
            Price.product,
            func.avg(Price.price).label('average_price')
        ).filter(Price.market_id == market_id).group_by(Price.product).all()

        # Convert the result to a list of dictionaries
        return [{'product': row[0], 'average_price': row[1]} for row in avg_prices]
    except Exception as e:
        print(f"Error calculating average prices: {e}")
        return []