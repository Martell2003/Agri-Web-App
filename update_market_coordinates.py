from app import create_app, db
from app.models.market import Market

# Create the Flask app and set up the app context
app = create_app()
app.app_context().push()

def update_market_coordinates():
    try:
        # Existing Markets
        nairobi_supermarkets = Market.query.filter_by(name="Nairobi Supermarkets").first()
        cheptulu = Market.query.filter_by(name="Cheptulu").first()
        kakamega_town = Market.query.filter_by(name="Kakamega Town").first()

        if nairobi_supermarkets:
            nairobi_supermarkets.latitude = -1.286389
            nairobi_supermarkets.longitude = 36.817223
            print("Updated coordinates for Nairobi Supermarkets")

        if cheptulu:
            cheptulu.latitude = 0.083333
            cheptulu.longitude = 34.716667
            print("Updated coordinates for Cheptulu")

        if kakamega_town:
            kakamega_town.latitude = 0.282731
            kakamega_town.longitude = 34.751966
            print("Updated coordinates for Kakamega Town")

        # New Markets in Kericho
        markets_coordinates = {
            "Kabianga Shopping Center": (-0.557022, 35.364246),
            "Chepnyogaa Market": (-0.539953, 35.339772),
            "Kapkatet Market": (-0.451532, 35.305664),
            "Litein Market": (-0.350041, 35.302014),
            "Sosiot Market": (-0.570516, 35.381547),
            "Kapkugerwet Market": (-0.527426, 35.320585),
        }

        for market_name, (lat, lon) in markets_coordinates.items():
            market = Market.query.filter_by(name=market_name).first()
            if market:
                market.latitude = lat
                market.longitude = lon
                print(f"Updated coordinates for {market_name}")
            else:
                print(f"Market {market_name} not found in database!")

        # Bomet County Markets Coordinates
        bomet_markets_coordinates = {
            "Bomet Town": (-0.80150090, 35.30272260),
            "Silibwet": (-0.73034, 35.34609),
            "Longisa": (-0.8605925, 35.3911901),
            "Mogogosiek": (-0.6186, 35.27217),
            "Kapkwen": (-0.78683, 35.2993),
            "Chebole": (-0.75131, 35.21475),
            "Kaplong": (-0.67816, 35.13915),
            "Litein": (-0.5833, 35.1833),
            "Sigor": (1.49597, 35.4727)  # Note: Sigor is in West Pokot, near Bomet
        }

        for market_name, coords in bomet_markets_coordinates.items():
            market = Market.query.filter_by(name=market_name).first()
            if market:
                if coords:
                    market.latitude, market.longitude = coords
                    print(f"Updated coordinates for {market_name}")
                else:
                    print(f"Coordinates for {market_name} not found; skipping update.")
            else:
                print(f"Market {market_name} not found in database!")

        # Commit all changes
        db.session.commit()
        print("Market coordinates updated successfully!")

    except Exception as e:
        print(f"Error updating coordinates: {e}")
        db.session.rollback()

if __name__ == "__main__":
    update_market_coordinates()
    print("Market coordinates update script executed.")
