import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import Select
from app.extensions import db
from app.models.price import Price
from app.models.product import Product
from app.models.market import Market
from datetime import datetime


def scrape_prices(county="Nairobi", entries_per_page=10):
    url = "https://amis.co.ke/site/market_search"
    
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(url)
        
        # Apply filter for County
        county_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "county[]"))
        )
        select = Select(county_dropdown)
        select.select_by_visible_text(county)

        # Set entries per page
        entries_dropdown = driver.find_element(By.NAME, "per_page")
        select = Select(entries_dropdown)
        select.select_by_value(str(entries_per_page))

        # Click "Filter Prices" button
        filter_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Filter Prices')]")
        filter_button.click()

        all_prices = []
        page = 1

        while True:
            # Wait for the table to load
            table = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Wait for rows to be visible
            rows = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tr"))
            )[1:]  # Skip header
            if not rows:
                print(f"No rows found on page {page}. Stopping.")
                break

            for row in rows:
                # Wait for columns to be visible
                cols = WebDriverWait(row, 10).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "td"))
                )
                if len(cols) < 10:
                    print(f"Skipping row with insufficient columns: {len(cols)}")
                    continue

                # Extract text safely
                try:
                    market_name = cols[0].text.strip() if cols[0].text else "Unknown Market"
                    product_name = cols[1].text.strip() if cols[1].text else "Unknown Product"
                    wholesale_price = cols[5].text.strip().replace('/Kg', '') if cols[5].text else "0.00"
                    county = cols[8].text.strip() if cols[8].text else "Unknown County"
                    date_str = cols[9].text.strip() if cols[9].text else datetime.now().strftime('%Y-%m-%d')
                except Exception as e:
                    print(f"Error extracting text from row: {e}")
                    continue

                # Debug: Print extracted values
                print(f"Row data - Market: {market_name} (type: {type(market_name)}), "
                      f"Product: {product_name} (type: {type(product_name)}), "
                      f"Price: {wholesale_price}, County: {county}, Date: {date_str}")

                # Ensure values are strings
                if not isinstance(market_name, str) or not isinstance(product_name, str):
                    print(f"Error: market_name or product_name is not a string. Market: {market_name}, Product: {product_name}")
                    continue

                # Parse price
                try:
                    price_value = float(wholesale_price)
                except ValueError:
                    print(f"Skipping row due to invalid price: {wholesale_price}")
                    continue

                # Parse date
                try:
                    timestamp = datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    print(f"Invalid date format: {date_str}. Using current timestamp.")
                    timestamp = datetime.now()

                # Fetch or create Product and Market
                try:
                    product = Product.query.filter_by(name=product_name).first()
                    if not product:
                        product = Product(name=product_name)
                        db.session.add(product)

                    market = Market.query.filter_by(name=market_name).first()
                    if not market:
                        market = Market(name=market_name, region_id=1)
                        db.session.add(market)

                    db.session.flush()

                    price = Price(
                        product_id=product.id,
                        market_id=market.id,
                        price=price_value,
                        timestamp=timestamp
                    )
                    all_prices.append(price)
                except Exception as e:
                    print(f"Error saving to database: {e}")
                    continue

            # Check for next page
            try:
                next_button = driver.find_element(By.LINK_TEXT, "Next")
                next_button.click()
                WebDriverWait(driver, 10).until(EC.staleness_of(table))
                page += 1
            except:
                print(f"No more pages after page {page}.")
                break

        if all_prices:
            db.session.add_all(all_prices)
            db.session.commit()
            print(f"Scraped and saved {len(all_prices)} price entries from KAMIS (County: {county}).")
        else:
            print("No prices scraped.")
        return all_prices

    except Exception as e:
        print(f"Error scraping KAMIS: {e}")
        return []
    finally:
        driver.quit()

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        scrape_prices(county="Nairobi")