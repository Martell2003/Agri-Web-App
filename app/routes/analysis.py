from flask import Blueprint, app, render_template, request, flash
from sqlalchemy import and_, cast
from ..models import Price, Market, Region
from ..analysis.charts import generate_matplotlib_chart, generate_plotly_chart
from ..analysis.stats import calculate_average_prices, calculate_price_variance
from flask_login import login_required
import plotly
import json
import plotly.express as px
from app.models import Product
from app.analysis import maps
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from app.extensions import db
from flask_paginate import Pagination, get_page_args, get_page_parameter
from sqlalchemy.types import Date
from datetime import timedelta

from flask import Blueprint, render_template, request, flash
from sqlalchemy import and_
from ..models import Price, Market, Region, Product
from app.analysis import maps
from datetime import datetime
from flask_login import login_required
import plotly.express as px
import json
import logging
from app.extensions import db
from flask_paginate import Pagination, get_page_args, get_page_parameter

print("Loading app/routes/analysis.py from", __file__)

analysis_bp = Blueprint('analysis', __name__, template_folder='templates/analysis')

@analysis_bp.route('/charts')
@login_required
def charts():
    logger = logging.getLogger(__name__)
    prices = Price.query.join(Product).join(Market).all()

    if prices:
        data = {
            'date': [price.timestamp.strftime('%Y-%m-%d') for price in prices],
            'price': [price.price for price in prices],
            'product': [price.product.name for price in prices],
            'market': [price.market.name for price in prices]
        }
        fig = px.line(
            data,
            x='date',
            y='price',
            color='product',
            line_group='market',
            title='Price Trends by Product',
            labels={'date': 'Date', 'price': 'Price (KES)', 'product': 'Product'}
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Price (KES)",
            legend_title="Product",
            hovermode="x unified"
        )
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        graph_json = json.dumps({"data": [], "layout": {"title": "No Data Available"}}, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('analysis/charts.html', graph_json=graph_json)

@analysis_bp.route('/trends', methods=['GET', 'POST'])
@login_required
def trends():
    logger = logging.getLogger(__name__)
    products = Product.query.all()
    markets = Market.query.all()
    product_filter = request.args.get('product')
    market_filter = request.args.get('market')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    search_query = request.args.get('search')
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 10

    query = Price.query.join(Product).join(Market, Price.market_id == Market.id)

    if product_filter and product_filter != 'all':
        query = query.filter(Product.name == product_filter)
        logger.debug(f"Applied product filter: {product_filter}")
    if market_filter and market_filter != 'all':
        query = query.filter(Market.name == market_filter)
        logger.debug(f"Applied market filter: {market_filter}")
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            query = query.filter(Price.timestamp >= start_date)
            logger.debug(f"Applied start date filter: {start_date}")
        except ValueError:
            flash('Invalid start date format. Please use YYYY-MM-DD.', 'danger')
            return render_template('analysis/trends.html', products=products, markets=markets)
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            query = query.filter(Price.timestamp <= end_date)
            logger.debug(f"Applied end date filter: {end_date}")
        except ValueError:
            flash('Invalid end date format. Please use YYYY-MM-DD.', 'danger')
            return render_template('analysis/trends.html', products=products, markets=markets)
    if search_query:
        query = query.filter((Product.name.ilike(f'%{search_query}%')) | (Market.name.ilike(f'%{search_query}%')))
        logger.debug(f"Applied search query: {search_query}")

    query = query.order_by(Price.timestamp.desc())
    prices_for_chart = query.all()
    logger.debug(f"Prices for chart: {len(prices_for_chart)}")

    if prices_for_chart:
        data = {
            'date': [price.timestamp.strftime('%Y-%m-%d') for price in prices_for_chart],
            'price': [price.price for price in prices_for_chart],
            'product': [price.product.name for price in prices_for_chart],
            'market': [price.market.name for price in prices_for_chart]
        }
        fig = px.line(
            data,
            x='date',
            y='price',
            color='product',
            line_group='market',
            title='Filtered Price Trends',
            labels={'date': 'Date', 'price': 'Price (KES)', 'product': 'Product'}
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Price (KES)",
            legend_title="Product",
            hovermode="x unified"
        )
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        graph_json = json.dumps({"data": [], "layout": {"title": "No Data Available"}}, cls=plotly.utils.PlotlyJSONEncoder)

    paginated_prices = query.paginate(page=page, per_page=per_page)
    table_data = [(price, price.product.name, price.market.name, price.market.region.name) for price in paginated_prices.items]
    pagination = Pagination(page=page, total=query.count(), per_page=per_page, record_name='prices')
    logger.debug(f"Paginated prices count: {len(table_data)}")

    return render_template(
        'analysis/trends.html',
        products=products,
        markets=markets,
        product_filter=product_filter,
        market_filter=market_filter,
        start_date=start_date_str,
        end_date=end_date_str,
        search_query=search_query,
        graph_json=graph_json,
        paginated_prices=table_data,
        pagination=pagination
    )

@analysis_bp.route('/maps')
@login_required
def map_view():
    logger = logging.getLogger(__name__)
    product_filter = request.form.get('product') if request.method == 'POST' else request.args.get('product')
    market_filter = request.form.get('market') if request.method == 'POST' else request.args.get('market')
    start_date = request.form.get('start_date') if request.method == 'POST' else request.args.get('start_date')
    end_date = request.form.get('end_date') if request.method == 'POST' else request.args.get('end_date')
    search_query = request.form.get('search') if request.method == 'POST' else request.args.get('search')

    products = Product.query.all()
    markets = Market.query.all()

    try:
        folium_map = maps.generate_folium_map(
            product_filter=product_filter,
            market_filter=market_filter,
            start_date=start_date,
            end_date=end_date,
            search_query=search_query
        )
    except Exception as e:
        logger.error(f"Error generating map: {str(e)}")
        flash(f'Error generating map: {str(e)}', 'danger')
        folium_map = maps.generate_folium_map()

    return render_template(
        'analysis/maps.html',
        map_html=folium_map._repr_html_(),
        products=products,
        markets=markets,
        product_filter=product_filter,
        market_filter=market_filter,
        start_date=start_date,
        end_date=end_date,
        search_query=search_query
    )

@analysis_bp.route('/stats')
@login_required
def stats():
    logger = logging.getLogger(__name__)
    product_filter = request.form.get('product') if request.method == 'POST' else request.args.get('product')
    market_filter = request.form.get('market') if request.method == 'POST' else request.args.get('market')
    start_date = request.form.get('start_date') if request.method == 'POST' else request.args.get('start_date')
    end_date = request.form.get('end_date') if request.method == 'POST' else request.args.get('end_date')
    search_query = request.form.get('search') if request.method == 'POST' else request.args.get('search')

    products_query = Product.query
    if product_filter and product_filter != "all":
        products_query = products_query.filter(Product.name == product_filter)
    if search_query:
        products_query = products_query.filter(Product.name.ilike(f"%{search_query}%"))
    products = products_query.all()

    stats = []
    for product in products:
        price_query = Price.query.filter_by(product_id=product.id)
        if market_filter and market_filter != "all":
            price_query = price_query.join(Market).filter(Market.name == market_filter)
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                price_query = price_query.filter(Price.timestamp >= start_date)
            except ValueError:
                logger.warning(f"Invalid start date: {start_date}")
                flash('Invalid start date format. Use YYYY-MM-DD.', 'danger')
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                price_query = price_query.filter(Price.timestamp <= end_date)
            except ValueError:
                logger.warning(f"Invalid end date: {end_date}")
                flash('Invalid end date format. Use YYYY-MM-DD.', 'danger')
        prices = [price.price for price in price_query.all()]
        if prices:
            stats.append({
                'product': product.name,
                'avg_price': round(sum(prices) / len(prices), 2),
                'min_price': min(prices),
                'max_price': max(prices),
                'num_markets': len(set(price.market_id for price in price_query.all()))
            })

    all_products = Product.query.all()
    markets = Market.query.all()

    return render_template(
        'analysis/stats.html',
        stats=stats,
        products=all_products,
        markets=markets,
        product_filter=product_filter,
        market_filter=market_filter,
        start_date=start_date,
        end_date=end_date,
        search_query=search_query
    )

@analysis_bp.route('/predict', methods=['GET', 'POST'])
@login_required
def predict_price():
    logger = logging.getLogger(__name__)
    logger.info(f"datetime.timedelta: {datetime.timedelta}")
    products = Product.query.all()
    markets = Market.query.all()

    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        market_id = request.form.get('market_id', type=int)
        days_ahead = request.form.get('days_ahead', type=int, default=7)

        if not product_id or not market_id:
            flash('Please select a product and a market.', 'danger')
            logger.warning(f"Missing product_id or market_id: product_id={product_id}, market_id={market_id}")
            return render_template('analysis/predict.html', products=products, markets=markets)

        try:
            product = Product.query.get_or_404(product_id)
            market = Market.query.get_or_404(market_id)

            prices = Price.query.filter_by(product_id=product_id, market_id=market_id).order_by(Price.timestamp).all()
            if not prices or len(prices) < 5:
                flash('Not enough historical data to make a prediction. Please add more price data.', 'danger')
                logger.warning(f"Insufficient data for product_id={product_id}, market_id={market_id}, prices_count={len(prices)}")
                return render_template('analysis/predict.html', products=products, markets=markets)

            import pandas as pd
            from sklearn.linear_model import LinearRegression

            dates = [price.timestamp for price in prices]
            prices_values = [price.price for price in prices]
            df = pd.DataFrame({'date': dates, 'price': prices_values})
            start_date = df['date'].min()
            df['days'] = (df['date'] - start_date).dt.days
            X = df[['days']].values
            y = df['price'].values
            model = LinearRegression()
            model.fit(X, y)
            last_day = df['days'].max()
            future_day = last_day + days_ahead
            future_price = model.predict([[future_day]])[0]
            prediction_date = start_date + datetime.timedelta(days=int(future_day))

            logger.info(f"Prediction for {product.name} at {market.name}: {future_price:.2f} KES on {prediction_date}")

            result = {
                'product_name': product.name,
                'market_name': market.name,
                'prediction_date': prediction_date.strftime('%Y-%m-%d'),
                'predicted_price': round(future_price, 2),
                'days_ahead': days_ahead
            }

            return render_template('analysis/predict.html', products=products, markets=markets, result=result)

        except Exception as e:
            flash(f'Error making prediction: {str(e)}', 'danger')
            logger.error(f"Prediction error: {str(e)}")
            return render_template('analysis/predict.html', products=products, markets=markets)

    return render_template('analysis/predict.html', products=products, markets=markets)

@analysis_bp.route('/compare', methods=['GET', 'POST'])
@login_required
def compare():
    logger = logging.getLogger(__name__)
    products = Product.query.all()
    markets = Market.query.all()
    default_graphJSON = json.dumps({"data": [], "layout": {}}, cls=plotly.utils.PlotlyJSONEncoder)

    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        market_ids = request.form.getlist('market_ids', type=int)
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        if not product_id or not market_ids or not start_date or not end_date:
            flash('Please select a product, at least one market, and a date range.', 'danger')
            logger.warning(f"Missing form data: product_id={product_id}, market_ids={market_ids}, start_date={start_date}, end_date={end_date}")
            return render_template('analysis/compare.html', products=products, markets=markets, graphJSON=default_graphJSON)

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            if start_date > end_date:
                flash('Start date must be before end date.', 'danger')
                logger.warning(f"Invalid date range: start_date={start_date} > end_date={end_date}")
                return render_template('analysis/compare.html', products=products, markets=markets, graphJSON=default_graphJSON)
        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
            logger.warning(f"Invalid date format: start_date={start_date}, end_date={end_date}")
            return render_template('analysis/compare.html', products=products, markets=markets, graphJSON=default_graphJSON)

        prices = Price.query.filter(
            and_(
                Price.product_id == product_id,
                Price.market_id.in_(market_ids),
                Price.timestamp >= start_date,
                Price.timestamp <= end_date
            )
        ).order_by(Price.timestamp).all()

        if not prices:
            flash('No price data found for the selected criteria.', 'danger')
            logger.warning(f"No prices found for product_id={product_id}, market_ids={market_ids}")
            return render_template('analysis/compare.html', products=products, markets=markets, graphJSON=default_graphJSON)

        product = Product.query.get(product_id)
        market_dict = {m.id: m.name for m in Market.query.filter(Market.id.in_(market_ids)).all()}
        table_data = [
            {
                'market': market_dict[p.market_id],
                'price': p.price,
                'timestamp': p.timestamp.strftime('%Y-%m-%d')
            } for p in prices
        ]
        data = {
            'timestamp': [p.timestamp for p in prices],
            'price': [p.price for p in prices],
            'market': [market_dict[p.market_id] for p in prices]
        }
        fig = px.line(
            data,
            x='timestamp',
            y='price',
            color='market',
            title=f'Price Comparison for {product.name} Across Markets',
            labels={'timestamp': 'Date', 'price': 'Price (KES)', 'market': 'Market'}
        )
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template(
            'analysis/compare.html',
            products=products,
            markets=markets,
            table_data=table_data,
            product_name=product.name,
            graphJSON=graphJSON
        )

    default_end = datetime.now()
    default_start = default_end - timedelta(days=30)
    return render_template(
        'analysis/compare.html',
        products=products,
        markets=markets,
        default_start=default_start.strftime('%Y-%m-%d'),
        default_end=default_end.strftime('%Y-%m-%d'),
        graphJSON=default_graphJSON
    )