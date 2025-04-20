from ..models import Price

def calculate_average_prices():
    """
    Calculate the average price for each product.
    """
    # Fetch prices from the database
    prices = Price.query.all()

    # Group prices by product and calculate the average price
    from collections import defaultdict
    product_prices = defaultdict(list)
    for price in prices:
        product_prices[price.product.name].append(price.price)

    average_prices = {product: sum(prices) / len(prices) for product, prices in product_prices.items()}
    return average_prices

def calculate_price_variance():
    """
    Calculate the variance in prices for each product.
    """
    # Fetch prices from the database
    prices = Price.query.all()

    # Group prices by product and calculate the variance
    from collections import defaultdict
    import statistics
    product_prices = defaultdict(list)
    for price in prices:
        product_prices[price.product.name].append(price.price)

    price_variance = {product: statistics.variance(prices) for product, prices in product_prices.items()}
    return price_variance