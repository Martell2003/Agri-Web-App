import folium
from folium.plugins import MarkerCluster
from app.models import Price
from app.models import Market
from datetime import datetime
from app.models import Product

def generate_folium_map(product_filter=None, market_filter=None, start_date=None, end_date=None, search_query=None):
    # Start with a base map centered on Kenya
    m = folium.Map(location=[0.0236, 37.9062], zoom_start=6)

    # Start with a base query for markets
    markets = Market.query

    # Apply market filter
    if market_filter and market_filter != "all":
        markets = markets.filter(Market.name == market_filter)

    # Execute the query to get filtered markets
    markets = markets.all()

    # For each market, get the latest price with the applied filters
    for market in markets:
        # Skip markets without coordinates
        if market.latitude is None or market.longitude is None:
            continue

        # Start with a base query for prices
        price_query = Price.query.filter_by(market_id=market.id)

        # Apply product filter
        if product_filter and product_filter != "all":
            price_query = price_query.join(Product).filter(Product.name == product_filter)

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

        # Apply search query
        if search_query:
            price_query = price_query.join(Product).filter(Product.name.ilike(f"%{search_query}%"))

        # Get the latest price for this market with the applied filters
        latest_price = price_query.order_by(Price.timestamp.desc()).first()
        if latest_price:
            # Add a marker for the market
            folium.Marker(
                location=(market.latitude, market.longitude),
                popup=f"{market.name}: {latest_price.product.name} - {latest_price.price} KES",
                icon=folium.Icon(color="green")
            ).add_to(m)

    return m