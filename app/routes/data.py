from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Product, Market, Price, Region
from app.data.scraper import KenyanAgriculturalPriceScraper
from app.data.processor import DataProcessor
from app.analysis.stats import calculate_average_prices
import logging
from datetime import datetime, timedelta

data_bp = Blueprint('data', __name__)
logger = logging.getLogger(__name__)

@data_bp.route('/data-management')
@login_required
def data_management():
    """Main data management dashboard"""
    return render_template('data/management.html')

@data_bp.route('/scrape', methods=['GET', 'POST'])
@login_required
def scrape():
    """Trigger price data scraping with optional parameters"""
    if request.method == 'POST':
        # Handle form submission with filters
        market_id = request.form.get('market_id')
        commodity_id = request.form.get('commodity_id')
        date = request.form.get('date')
        
        try:
            scraper = KenyanAgriculturalPriceScraper()
            success_count, error_count = scraper.scrape_and_save_prices(
                market_id=market_id,
                commodity_id=commodity_id,
                date=date
            )
            
            if success_count > 0:
                flash(f"Successfully saved {success_count} price records", 'success')
                if error_count > 0:
                    flash(f"{error_count} records failed to save", 'warning')
            else:
                flash("No new price records were saved", 'warning')
                
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}", exc_info=True)
            flash(f"Scraping failed: {str(e)}", 'danger')
            
        return redirect(url_for('data.data_management'))
    
    # GET request - show scraping form
    markets = Market.query.order_by(Market.name).all()
    products = Product.query.order_by(Product.name).all()
    return render_template('data/scrape.html', markets=markets, products=products)

@data_bp.route('/clean-data', methods=['POST'])
@login_required
def clean_data():
    """Clean old data based on parameters"""
    try:
        days = int(request.form.get('days', 30))
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Count before deletion for reporting
        count_before = Price.query.count()
        
        # Delete old prices
        Price.query.filter(Price.date < cutoff_date).delete()
        
        # Optionally clean orphaned markets and products
        # (Add similar logic if needed)
        
        db.session.commit()
        
        count_after = Price.query.count()
        records_deleted = count_before - count_after
        
        flash(f"Successfully cleaned {records_deleted} records older than {days} days", 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Data cleaning failed: {str(e)}", exc_info=True)
        flash(f"Data cleaning failed: {str(e)}", 'danger')
    
    return redirect(url_for('data.data_management'))

@data_bp.route('/average-prices')
@login_required
def average_prices():
    """Display average prices with filters"""
    market_id = request.args.get('market_id')
    product_id = request.args.get('product_id')
    time_range = request.args.get('time_range', '30')  # days
    
    try:
        avg_prices = calculate_average_prices(
            market_id=market_id,
            product_id=product_id,
            days=int(time_range)
        )
        
        markets = Market.query.order_by(Market.name).all()
        products = Product.query.order_by(Product.name).all()
        
        return render_template(
            'data/average_prices.html',
            avg_prices=avg_prices,
            markets=markets,
            products=products,
            selected_market=market_id,
            selected_product=product_id,
            selected_range=time_range
        )
    except Exception as e:
        logger.error(f"Average price calculation failed: {str(e)}", exc_info=True)
        flash("Failed to calculate average prices", 'danger')
        return redirect(url_for('data.data_management'))

@data_bp.route('/api/scrape-status')
@login_required
def scrape_status():
    """API endpoint to check recent scraping activity"""
    last_scrape = Price.query.order_by(Price.scraped_at.desc()).first()
    
    return jsonify({
        'last_scraped': last_scrape.scraped_at.isoformat() if last_scrape else None,
        'record_count': Price.query.count()
    })

@data_bp.route('/api/market-products')
@login_required
def market_products():
    """API endpoint to get products for a specific market"""
    market_id = request.args.get('market_id')
    if not market_id:
        return jsonify([])
    
    products = db.session.query(Product).join(Price).filter(
        Price.market_id == market_id
    ).distinct().all()
    
    return jsonify([{
        'id': p.id,
        'name': p.name
    } for p in products])

@data_bp.route('/api/recent-prices')
@login_required
def recent_prices():
    """Get recently scraped prices for the table"""
    recent = Price.query.join(Product).join(Market)\
              .order_by(Price.scraped_at.desc())\
              .limit(10)\
              .all()
    
    return jsonify([{
        'date': p.date.isoformat(),
        'market_name': p.market.name,
        'product_name': p.product.name,
        'wholesale_price': p.wholesale_price,
        'retail_price': p.retail_price,
        'unit': p.unit
    } for p in recent])

@data_bp.route('/api/data-stats')
@login_required
def data_stats():
    """Get database statistics for the dashboard"""
    return jsonify({
        'price_records': Price.query.count(),
        'market_count': Market.query.count(),
        'product_count': Product.query.count(),
        'last_update': Price.query.order_by(Price.scraped_at.desc())
                      .first().scraped_at.isoformat() if Price.query.first() else None
    })

@data_bp.route('/api/activity-log')
@login_required
def activity_log():
    """Get recent scraping/maintenance activity"""
    # In a real implementation, you would query an ActivityLog model
    return jsonify([
        {
            'timestamp': datetime.now().isoformat(),
            'action': 'Data Scrape',
            'records_affected': 42,
            'status': 'success',
            'details': 'Fetched latest prices'
        },
        # Add more sample or real activities
    ])