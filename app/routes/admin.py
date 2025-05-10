from flask import Blueprint, flash, redirect, url_for
from flask_login import login_required
from app.data.scraper import scrape_indexmundi_maize
from app.data.processor import process_price_data
import logging

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

@admin_bp.route('/scrape', methods=['GET'])
@login_required
def run_scraper():
    """Manually trigger the scraper."""
    try:
        price_data = scrape_indexmundi_maize()
        new_prices = process_price_data(price_data)
        flash(f'Scraping completed, saved {new_prices} new prices.', 'success')
    except Exception as e:
        logger.error(f"Manual scraping failed: {str(e)}")
        flash(f'Scraping failed: {str(e)}', 'danger')
    return redirect(url_for('admin.index'))  # Adjust to your admin dashboard