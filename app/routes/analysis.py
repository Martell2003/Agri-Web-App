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

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/charts')
def charts():
    # Fetch prices from the database
    prices = Price.query.all()

    # Convert prices to a list of dictionaries
    price_data = [{'product': price.product, 'price': price.price} for price in prices]

    #debug: Print the Price data
    print("Price Data for Chats:", price_data)

    # Generate charts
    matplotlib_chart = generate_matplotlib_chart(price_data)
    plotly_chart = generate_plotly_chart(price_data)

    return render_template('analysis/charts.html', matplotlib_chart=matplotlib_chart, plotly_chart=plotly_chart)

@analysis_bp.route('/trends', methods=['GET', 'POST'])
@login_required
def trends():
    import logging
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

    # Chart data
    prices_for_chart = query.all()
    logger.debug(f"Prices for chart: {len(prices_for_chart)}")
    if prices_for_chart:
        logger.debug(f"Sample price data: {[(p.product.name, p.market.name, p.price, p.timestamp) for p in prices_for_chart[:3]]}")
    
    chart_data = {}
    if prices_for_chart:
        for price in prices_for_chart:
            product_name = price.product.name
            if product_name not in chart_data:
                chart_data[product_name] = {'dates': [], 'prices': []}
            chart_data[product_name]['dates'].append(price.timestamp.strftime('%Y-%m-%d'))
            chart_data[product_name]['prices'].append(price.price)
    
    graph_json = []
    for product_name, data in chart_data.items():
        graph_json.append({
            'x': data['dates'],
            'y': data['prices'],
            'type': 'scatter',
            'name': product_name
        })
    logger.debug(f"Graph JSON data: {graph_json}")
    graph_json = json.dumps({"data": graph_json, "layout": {}}, cls=plotly.utils.PlotlyJSONEncoder)
    logger.debug(f"Serialized graphJSON: {graph_json}")

    # Table data
    paginated_prices = query.paginate(page=page, per_page=per_page)
    table_data = []
    for price in paginated_prices.items:
        product_name = price.product.name
        market_name = price.market.name
        region_name = price.market.region.name
        table_data.append((price, product_name, market_name, region_name))
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
        graphJSON=graph_json,
        paginated_prices=table_data,
        pagination=pagination
    )

@analysis_bp.route('/maps')
@login_required
def map_view():
    # Get filter parameters from the form (if submitted)
    product_filter = request.form.get('product') if request.method == 'POST' else request.args.get('product')
    market_filter = request.form.get('market') if request.method == 'POST' else request.args.get('market')
    start_date = request.form.get('start_date') if request.method == 'POST' else request.args.get('start_date')
    end_date = request.form.get('end_date') if request.method == 'POST' else request.args.get('end_date')
    search_query = request.form.get('search') if request.method == 'POST' else request.args.get('search')

    # Get all products and markets for the filter dropdowns
    products = Product.query.all()
    markets = Market.query.all()

    # Generate the Folium map with the applied filters
    folium_map = maps.generate_folium_map(
        product_filter=product_filter,
        market_filter=market_filter,
        start_date=start_date,
        end_date=end_date,
        search_query=search_query
    )

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
    # Get filter parameters from the form (if submitted)
    product_filter = request.form.get('product') if request.method == 'POST' else request.args.get('product')
    market_filter = request.form.get('market') if request.method == 'POST' else request.args.get('market')
    start_date = request.form.get('start_date') if request.method == 'POST' else request.args.get('start_date')
    end_date = request.form.get('end_date') if request.method == 'POST' else request.args.get('end_date')
    search_query = request.form.get('search') if request.method == 'POST' else request.args.get('search')

    # Get all products
    products_query = Product.query

    # Apply product filter to the products query
    if product_filter and product_filter != "all":
        products_query = products_query.filter(Product.name == product_filter)

    # Apply search query to the products query
    if search_query:
        products_query = products_query.filter(Product.name.ilike(f"%{search_query}%"))

    # Execute the query to get filtered products
    products = products_query.all()

    # Calculate statistics with the applied filters
    stats = []
    for product in products:
        # Start with a base query for prices
        price_query = Price.query.filter_by(product_id=product.id)

        # Apply market filter
        if market_filter and market_filter != "all":
            price_query = price_query.join(Market).filter(Market.name == market_filter)

        # Apply date range filter
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                price_query = price_query.filter(Price.timestamp >= start_date)
            except ValueError:
                print(f"Invalid start date: {start_date}")
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                price_query = price_query.filter(Price.timestamp <= end_date)
            except ValueError:
                print(f"Invalid end date: {end_date}")

        # Get the filtered prices
        prices = [price.price for price in price_query.all()]
        if prices:
            stats.append({
                'product': product.name,
                'avg_price': sum(prices) / len(prices),
                'min_price': min(prices),
                'max_price': max(prices),
                'num_markets': len(set(price.market_id for price in price_query.all()))
            })

    # Get all products and markets for the filter dropdowns
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
#@login_required # Removed to run the code
def predict_price():
    # Fetch all products and markets for the dropdowns
    products = Product.query.all()
    markets = Market.query.all()

    if request.method == 'POST':
        # Get form data
        product_id = request.form.get('product_id', type=int)
        market_id = request.form.get('market_id', type=int)
        days_ahead = request.form.get('days_ahead', type=int, default=7)

        if not product_id or not market_id:
            flash('Please select a product and a market.', 'danger')
            return render_template('analysis/predict.html', products=products, markets=markets)

        # Fetch historical price data
        prices = Price.query.filter_by(product_id=product_id, market_id=market_id).order_by(Price.timestamp).all()

        if not prices or len(prices) < 5:  # Require at least 5 data points for a meaningful prediction
            flash('Not enough historical data to make a prediction. Please add more price data.', 'danger')
            return render_template('analysis/predict.html', products=products, markets=markets)

        # Prepare data for the model
        # Convert timestamps to numerical values (days since the earliest date)
        dates = [price.timestamp for price in prices]
        prices_values = [price.price for price in prices]

        # Create a DataFrame
        df = pd.DataFrame({
            'date': dates,
            'price': prices_values
        })

        # Convert dates to numerical values (days since the first date)
        start_date = df['date'].min()
        df['days'] = (df['date'] - start_date).dt.days

        # Prepare features (X) and target (y)
        X = df[['days']].values  # Feature: number of days
        y = df['price'].values  # Target: price

        # Train a linear regression model
        model = LinearRegression()
        model.fit(X, y)

        # Predict the price for the future date
        last_day = df['days'].max()
        future_day = last_day + days_ahead
        future_price = model.predict([[future_day]])[0]

        # Calculate the prediction date
        prediction_date = start_date + timedelta(days=int(future_day)) # Convert to int

        # Prepare the result
        product = Product.query.get(product_id)
        market = Market.query.get(market_id)
        result = {
            'product_name': product.name,
            'market_name': market.name,
            'prediction_date': prediction_date.strftime('%Y-%m-%d'),
            'predicted_price': round(future_price, 2),
            'days_ahead': days_ahead
        }

        return render_template('analysis/predict.html', products=products, markets=markets, result=result)

    return render_template('analysis/predict.html', products=products, markets=markets)


@analysis_bp.route('/compare', methods=['GET', 'POST'])
@login_required
def compare():
    products = Product.query.all()
    markets = Market.query.all()
    
    # Default graphJSON for GET requests (empty Plotly figure)
    default_graphJSON = json.dumps({"data": [], "layout": {}}, cls=plotly.utils.PlotlyJSONEncoder)
    
    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        market_ids = request.form.getlist('market_ids', type=int)  # Multiple markets
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        if not product_id or not market_ids or not start_date or not end_date:
            flash('Please select a product, at least one market, and a date range.', 'danger')
            return render_template('analysis/compare.html', 
                                products=products, 
                                markets=markets, 
                                graphJSON=default_graphJSON)
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            if start_date > end_date:
                flash('Start date must be before end date.', 'danger')
                return render_template('analysis/compare.html', 
                                    products=products, 
                                    markets=markets, 
                                    graphJSON=default_graphJSON)
        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
            return render_template('analysis/compare.html', 
                                products=products, 
                                markets=markets, 
                                graphJSON=default_graphJSON)
        
        # Fetch prices for the selected product and markets
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
            return render_template('analysis/compare.html', 
                                products=products, 
                                markets=markets, 
                                graphJSON=default_graphJSON)
        
        # Prepare data for table and chart
        product = Product.query.get(product_id)
        market_dict = {m.id: m.name for m in Market.query.filter(Market.id.in_(market_ids)).all()}
        
        # Table data
        table_data = [
            {
                'market': market_dict[p.market_id],
                'price': p.price,
                'timestamp': p.timestamp.strftime('%Y-%m-%d')
            } for p in prices
        ]
        
        # Plotly chart
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
        
        return render_template('analysis/compare.html',
                             products=products,
                             markets=markets,
                             table_data=table_data,
                             product_name=product.name,
                             graphJSON=graphJSON)
    
    # Default: Show last 30 days for GET request
    default_end = datetime.now()
    default_start = default_end - timedelta(days=30)
    
    return render_template('analysis/compare.html',
                          products=products,
                          markets=markets,
                          default_start=default_start.strftime('%Y-%m-%d'),
                          default_end=default_end.strftime('%Y-%m-%d'),
                          graphJSON=default_graphJSON)