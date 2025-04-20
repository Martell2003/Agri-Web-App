import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from io import BytesIO
import base64

def generate_matplotlib_chart(prices):
    """
    Generate a Matplotlib bar chart for agricultural prices.
    """
    try:
        #Ensure all records have the 'product' and 'price' keys
        prices = [p for p in prices if 'product' in p and 'price' in p]

        if not prices:
            print("No valid data to generate chart.")
            return None

        #debug: Print the prices data
        print("Prices Data:", prices)

        # Convert prices to a Pandas DataFrame
        df = pd.DataFrame(prices)

        # Create a bar chart
        plt.figure(figsize=(10, 6))
        plt.bar(df['product'], df['price'], color='skyblue')
        plt.xlabel('Product')
        plt.ylabel('Price')
        plt.title('Agricultural Product Prices')
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save the chart to a BytesIO object
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)

        # Convert the chart to a base64-encoded string
        chart_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()

        return chart_image
    except Exception as e:
        print(f"Error generating Matplotlib chart: {e}")
        return None

def generate_plotly_chart(prices):
    """
    Generate an interactive Plotly bar chart for agricultural prices.
    """
    try:
        # Convert prices to a Pandas DataFrame
        df = pd.DataFrame(prices)

        # Create an interactive bar chart
        fig = px.bar(df, x='product', y='price', title='Agricultural Product Prices',
                     labels={'product': 'Product', 'price': 'Price'})
        fig.update_layout(xaxis_tickangle=-45)

        # Convert the chart to HTML
        chart_html = fig.to_html(full_html=False)
        return chart_html
    except Exception as e:
        print(f"Error generating Plotly chart: {e}")
        return None
    
    #This function generates a Plotly line chart to visualize price trends over time.

def generate_plotly_chart(price_data):
    """
    Generate a Plotly line chart to visualize price trends over time.
    """
    if not price_data:
        return "<p>No data available for trends.</p>"

    # Convert data to a Pandas DataFrame
    df = pd.DataFrame(price_data)

    # Ensure the required columns exist
    if not all(col in df.columns for col in ['timestamp', 'price', 'product']):
        return "<p>Invalid data format for trends.</p>"

    # Create a line chart
    fig = px.line(df, x='timestamp', y='price', color='product',
                  labels={'timestamp': 'Date', 'price': 'Price', 'product': 'Product'},
                  title='Agricultural Price Trends Over Time')

    # Convert the chart to HTML
    return fig.to_html(full_html=False)