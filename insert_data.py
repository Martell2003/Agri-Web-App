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

        # Flush to assign IDs
        db.session.flush()

        # Step 2: Create Markets
        nairobi_supermarkets = Market.query.filter_by(name="Nairobi Supermarkets").first()
        if not nairobi_supermarkets:
            nairobi_supermarkets = Market(name="Nairobi Supermarkets", region_id=nairobi_region.id)
            db.session.add(nairobi_supermarkets)
            print("Added Market: Nairobi Supermarkets")

        cheptulu = Market.query.filter_by(name="Cheptulu").first()
        if not cheptulu:
            cheptulu = Market(name="Cheptulu", region_id=vihiga_region.id)
            db.session.add(cheptulu)
            print("Added Market: Cheptulu")

        kakamega_town = Market.query.filter_by(name="Kakamega Town").first()
        if not kakamega_town:
            kakamega_town = Market(name="Kakamega Town", region_id=kakamega_region.id)
            db.session.add(kakamega_town)
            print("Added Market: Kakamega Town")

        # Flush to assign IDs
        db.session.flush()

        # Step 3: Create Products
        products = [
            "Wheat Flour Soko Atta Mark 1",
            "Wheat Flour Winnie's Pure Health Atta Mark 1",
            "Wheat Flour Tropicana HBF",
            "Spinach",
            "Tomatoes",
            "Dry Onions",
            "Cabbages",
            "Banana (Cooking)",
            "Ethiopian Kales - Kanzira",
            "Jute Plant (Murenda)"
        ]

        for product_name in products:
            product = Product.query.filter_by(name=product_name).first()
            if not product:
                product = Product(name=product_name)
                db.session.add(product)
                print(f"Added Product: {product_name}")

        # Flush to assign IDs
        db.session.flush()

        # Step 4: Create Price Entries (data from KAMIS screenshot)
        price_data = [
            # Nairobi Supermarkets
            {
                "product_name": "Wheat Flour Soko Atta Mark 1",
                "market_name": "Nairobi Supermarkets",
                "price": 81.00,
                "timestamp": datetime(2025, 3, 26)
            },
            {
                "product_name": "Wheat Flour Winnie's Pure Health Atta Mark 1",
                "market_name": "Nairobi Supermarkets",
                "price": 128.50,
                "timestamp": datetime(2025, 3, 26)
            },
            {
                "product_name": "Wheat Flour Tropicana HBF",
                "market_name": "Nairobi Supermarkets",
                "price": 80.00,
                "timestamp": datetime(2025, 3, 26)
            },
            # Cheptulu (Vihiga)
            {
                "product_name": "Spinach",
                "market_name": "Cheptulu",
                "price": 60.00,
                "timestamp": datetime(2025, 3, 26)
            },
            {
                "product_name": "Tomatoes",
                "market_name": "Cheptulu",
                "price": 71.43,
                "timestamp": datetime(2025, 3, 26)
            },
            {
                "product_name": "Dry Onions",
                "market_name": "Cheptulu",
                "price": 80.00,
                "timestamp": datetime(2025, 3, 26)
            },
            {
                "product_name": "Cabbages",
                "market_name": "Cheptulu",
                "price": 30.77,
                "timestamp": datetime(2025, 3, 26)
            },
            {
                "product_name": "Banana (Cooking)",
                "market_name": "Cheptulu",
                "price": 38.46,
                "timestamp": datetime(2025, 3, 26)
            },
            {
                "product_name": "Ethiopian Kales - Kanzira",
                "market_name": "Cheptulu",
                "price": 60.00,
                "timestamp": datetime(2025, 3, 26)
            },
            {
                "product_name": "Jute Plant (Murenda)",
                "market_name": "Cheptulu",
                "price": 90.00,
                "timestamp": datetime(2025, 3, 26)
            },
            # Kakamega Town
            {
                "product_name": "Cabbages",
                "market_name": "Kakamega Town",
                "price": 15.00,
                "timestamp": datetime(2025, 3, 26)
            }
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

        # Commit all changes
        db.session.commit()
        print("Data insertion completed successfully!")

    except Exception as e:
        print(f"Error inserting data: {e}")
        db.session.rollback()

if __name__ == "__main__":
    insert_sample_data()