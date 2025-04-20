from flask import Blueprint, render_template, request, flash
from ..models import Price, Market
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

@analysis_bp.route('/trends')
@login_required
def trends():
# Get filter parameters from the form (if submitted)
    product_filter = request.form.get('product') if request.method == 'POST' else request.args.get('product')
    market_filter = request.form.get('market') if request.method == 'POST' else request.args.get('market')
    start_date = request.form.get('start_date') if request.method == 'POST' else request.args.get('start_date')
    end_date = request.form.get('end_date') if request.method == 'POST' else request.args.get('end_date')
    search_query = request.form.get('search') if request.method == 'POST' else request.args.get('search')

    # Start with a base query for prices
    query = Price.query

    # Apply product filter
    if product_filter and product_filter != "all":
        query = query.join(Product).filter(Product.name == product_filter)

    # Apply market filter
    if market_filter and market_filter != "all":
        query = query.join(Market).filter(Market.name == market_filter)

    # Apply date range filter
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Price.timestamp >= start_date)
        except ValueError:
            print(f"Invalid start date: {start_date}")
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(Price.timestamp <= end_date)
        except ValueError:
            print(f"Invalid end date: {end_date}")

    # Apply search query (filter products by name)
    if search_query:
        query = query.join(Product).filter(Product.name.ilike(f"%{search_query}%"))

    # Execute the query to get filtered prices
    prices = query.all()

    # Debug: Print the number of prices retrieved
    print(f"Number of prices retrieved: {len(prices)}")
    for price in prices:
        print(f"Price: {price.price}, Product: {price.product.name}, Market: {price.market.name}, Timestamp: {price.timestamp}")

    # Prepare data for plotting
    data = {
        'timestamp': [price.timestamp for price in prices],
        'price': [price.price for price in prices],
        'product': [price.product.name for price in prices],
        'market': [price.market.name for price in prices]
    }

    # Create a line plot
    fig = px.line(
        data,
        x='timestamp',
        y='price',
        color='product',
        line_group='market',
        hover_name='market',
        title='Price Trends Over Time'
    )

    # Convert the plot to JSON for rendering in the template
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Get all products and markets for the filter dropdowns
    products = Product.query.all()
    markets = Market.query.all()

    # Pass the current filter values to the template for form persistence
    return render_template(
        'analysis/trends.html',
        graphJSON=graphJSON,
        prices=prices,
        products=products,
        markets=markets,
        product_filter=product_filter,
        market_filter=market_filter,
        start_date=start_date,
        end_date=end_date,
        search_query=search_query
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
@login_required
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
        y = df['price'].values   # Target: price

        # Train a linear regression model
        model = LinearRegression()
        model.fit(X, y)

        # Predict the price for the future date
        last_day = df['days'].max()
        future_day = last_day + days_ahead
        future_price = model.predict([[future_day]])[0]

        # Calculate the prediction date
        prediction_date = start_date + timedelta(days=future_day)

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