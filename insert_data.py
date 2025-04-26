from app import create_app, db
from app.models.region import Region
from app.models.market import Market
from app.models.product import Product
from app.models.price import Price
from datetime import datetime

# Create the Flask app and set up the app context
app = create_app()
app.app_context().push()

def insert_sample_data():
    try:
        # Step 1: Create Regions
        nairobi_region = Region.query.filter_by(name="Nairobi").first()
        if not nairobi_region:
            nairobi_region = Region(name="Nairobi")
            db.session.add(nairobi_region)
            print("Added Region: Nairobi")

        vihiga_region = Region.query.filter_by(name="Vihiga").first()
        if not vihiga_region:
            vihiga_region = Region(name="Vihiga")
            db.session.add(vihiga_region)
            print("Added Region: Vihiga")

        kakamega_region = Region.query.filter_by(name="Kakamega").first()
        if not kakamega_region:
            kakamega_region = Region(name="Kakamega")
            db.session.add(kakamega_region)
            print("Added Region: Kakamega")

        kericho_region = Region.query.filter_by(name="Kericho").first()
        if not kericho_region:
            kericho_region = Region(name="Kericho")
            db.session.add(kericho_region)
            print("Added Region: Kericho")

        # Add Bomet Region
        bomet_region = Region.query.filter_by(name="Bomet").first()
        if not bomet_region:
            bomet_region = Region(name="Bomet")
            db.session.add(bomet_region)
            print("Added Region: Bomet")

        db.session.flush()

        # Step 2: Create Markets
        markets = {
            # Existing markets...
            "Nairobi Supermarkets": nairobi_region.id,
            "Cheptulu": vihiga_region.id,
            "Kakamega Town": kakamega_region.id,
            "Kericho Municipal Market": kericho_region.id,
            "Kapkatet Market": kericho_region.id,
            "Chepseon Market": kericho_region.id,
            "Chesinende Market": kericho_region.id,
            "Sosiot Market": kericho_region.id,
            "Fort Ternan Market": kericho_region.id,
            "Kabianga Shopping Centre": kericho_region.id,
            "Chepnyogaa Market": kericho_region.id,

            # Bomet County Markets
            "Bomet Town": bomet_region.id,
            "Silibwet": bomet_region.id,
            "Longisa": bomet_region.id,
            "Mogogosiek": bomet_region.id,
            "Kapkwen": bomet_region.id,
            "Chebole": bomet_region.id,
            "Kaplong": bomet_region.id,
            "Litein": bomet_region.id,
            "Sigor": bomet_region.id
        }

        for market_name, region_id in markets.items():
            market = Market.query.filter_by(name=market_name).first()
            if not market:
                market = Market(name=market_name, region_id=region_id)
                db.session.add(market)
                print(f"Added Market: {market_name}")

        db.session.flush()

        # Step 3: Create Products
        products = [
            # Existing products...
            "Wheat Flour Soko Atta Mark 1", "Wheat Flour Winnie's Pure Health Atta Mark 1",
            "Wheat Flour Tropicana HBF", "Spinach", "Tomatoes", "Dry Onions",
            "Cabbages", "Banana (Cooking)", "Ethiopian Kales - Kanzira", "Jute Plant (Murenda)",
            "Rice Basmati", "Rice Pishori", "Rice Sindano", "Rice Milled", "Rice Broken",
            "Maize", "Beans", "Irish Potatoes", "Cabbages (Large)", "Tomatoes (Fresh)",
            "Dairy Milk", "Tea Leaves", "Coffee", "Sugarcane", "Vegetables", "Fruits"
        ]

        for product_name in products:
            product = Product.query.filter_by(name=product_name).first()
            if not product:
                product = Product(name=product_name)
                db.session.add(product)
                print(f"Added Product: {product_name}")

        db.session.flush()

        # Step 4: Create Price Entries for Bomet Markets
        price_data = [
            # Bomet Town
            {"product_name": "Irish Potatoes", "market_name": "Bomet Town", "price": 28, "timestamp": datetime(2025, 4, 26)},
            {"product_name": "Tea Leaves", "market_name": "Bomet Town", "price": 25, "timestamp": datetime(2025, 4, 26)},
            {"product_name": "Dairy Milk", "market_name": "Bomet Town", "price": 55, "timestamp": datetime(2025, 4, 26)},

            # Silibwet
            {"product_name": "Irish Potatoes", "market_name": "Silibwet", "price": 26.67, "timestamp": datetime(2025, 4, 26)},
            {"product_name": "Tea Leaves", "market_name": "Silibwet", "price": 24, "timestamp": datetime(2025, 4, 26)},
            {"product_name": "Dairy Milk", "market_name": "Silibwet", "price": 54, "timestamp": datetime(2025, 4, 26)},

            # Longisa
            {"product_name": "Irish Potatoes", "market_name": "Longisa", "price": 27, "timestamp": datetime(2025, 4, 26)},
            {"product_name": "Tea Leaves", "market_name": "Longisa", "price": 26, "timestamp": datetime(2025, 4, 26)},
            {"product_name": "Dairy Milk", "market_name": "Longisa", "price": 56, "timestamp": datetime(2025, 4, 26)},

            # Mogogosiek
            {"product_name": "Irish Potatoes", "market_name": "Mogogosiek", "price": 27.27, "timestamp": datetime(2025, 4, 26)},
            {"product_name": "Tea Leaves", "market_name": "Mogogosiek", "price": 27, "timestamp": datetime(2025, 4, 26)},
            {"product_name": "Dairy Milk", "market_name": "Mogogosiek", "price": 57, "timestamp": datetime(2025, 4, 26)},

            # Kapkwen
            {"product_name": "Irish Potatoes", "market_name": "Kapkwen", "price": 27.27, "timestamp": datetime(2025, 4, 26)},
            {"product_name": "Tea Leaves", "market_name": "Kapkwen", "price": 25, "timestamp": datetime(2025, 4, 26)},
            {"product_name": "Dairy Milk", "market_name": "Kapkwen", "price": 55, "timestamp": datetime(2025, 4, 26)},

            # Chebole
            {"product_name": "Irish Potatoes", "market_name": "Chebole", "price": 27, "timestamp": datetime(2025, 4, 26)},
            {"product_name": "Tea Leaves", "market_name": "Chebole", "price": 24, "timestamp": datetime(2025, 4, 26)},
            {"product_name": "Dairy Milk", "market_name": "Chebole", "price": 54, "timestamp": datetime(2025, 4, 26)},

            # Kaplong
            {"product_name": "Irish Potatoes", "market_name": "Kaplong", "price": 27, "timestamp": datetime(2025, 4, 26)},
            {"product_name": "Tea Leaves", "market_name": "Kaplong", "price": 26, "timestamp": datetime(2025, 4, 26)},
            {"product_name": "Dairy Milk", "market_name": "Kaplong", "price": 56, "timestamp": datetime(2025, 4, 26)},

            # Litein
            {"product_name": "Irish Potatoes", "market_name": "Litein", "price": 27.59, "timestamp": datetime(2025, 4, 26)},
            {"product_name": "Tea Leaves", "market_name": "Litein", "price": 25, "timestamp": datetime(2025, 4, 26)},
            {"product_name": "Dairy Milk", "market_name": "Litein", "price": 55, "timestamp": datetime(2025, 4, 26)},

            # Sigor (Note: Sigor is near Bomet but in West Pokot; included here as per your data)
            {"product_name": "Irish Potatoes", "market_name": "Sigor", "price": 27, "timestamp": datetime(2025, 4, 26)},
            {"product_name": "Tea Leaves", "market_name": "Sigor", "price": 27, "timestamp": datetime(2025, 4, 26)},
            {"product_name": "Dairy Milk", "market_name": "Sigor", "price": 57, "timestamp": datetime(2025, 4, 26)},
        ]

        for entry in price_data:
            product = Product.query.filter_by(name=entry["product_name"]).first()
            market = Market.query.filter_by(name=entry["market_name"]).first()
            if product and market:
                price = Price(
                    product_id=product.id,
                    market_id=market.id,
                    price=entry["price"],
                    timestamp=entry["timestamp"]
                )
                db.session.add(price)
                print(f"Added Price: {product.name} at {market.name} - {entry['price']} KES")

        db.session.commit()
        print("Data insertion completed successfully!")

    except Exception as e:
        print(f"Error inserting data: {e}")
        db.session.rollback()

if __name__ == "__main__":
    insert_sample_data()
    print("Sample data inserted successfully.")
