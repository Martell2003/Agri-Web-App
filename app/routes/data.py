from flask import Blueprint, render_template, flash, redirect, url_for
from ..data.scraper import scrape_prices
from ..data.api_fetcher import fetch_prices
from ..data.processor import calculate_average_prices, save_prices
from ..models import Market
from app.models import Price

data_bp = Blueprint('data', __name__)


@data_bp.route('/scrape', methods=['GET'])
def scrape():
    # Fetch all prices from the database
    prices = Price.query.all()
    if prices:
        flash(f"Displaying {len(prices)} price entries from the database.", "success")
    else:
        flash("No prices found in the database.", "info")
    return render_template('data/prices.html', prices=prices)


#route to display average prices

@data_bp.route('/average_prices')
def average_prices():
    market_id = 1  # Replace with the actual market logic
    avg_prices = calculate_average_prices(market_id)
    return render_template('data/average_prices.html', avg_prices=avg_prices)