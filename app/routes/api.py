from flask import Blueprint, jsonify
from ..models import Price, Product, Market
from flask import request

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/prices', methods=['GET'])
def get_prices():
    """
    Get a list of all prices.
    """
    product= request.args.get('product', 'all')
    prices = Price.query.filter_by(product=product).all() if product != 'all' else Price.query.all()
    price_data = [{
        'id': price.id,
        'product': price.product.name,
        'market': price.market.name,
        'price': price.price,
        'timestamp': price.timestamp.isoformat(),
    } for price in prices]
    return jsonify(price_data)

@api_bp.route('/api/products', methods=['GET'])
def get_products():
    """
    Get a list of all products.
    """
    products = Product.query.all()
    product_data = [{
        'id': product.id,
        'name': product.name,
    } for product in products]
    return jsonify(product_data)

@api_bp.route('/api/markets', methods=['GET'])
def get_markets():
    """
    Get a list of all markets.
    """
    markets = Market.query.all()
    market_data = [{
        'id': market.id,
        'name': market.name,
        'region': market.region.name,
    } for market in markets]
    return jsonify(market_data)