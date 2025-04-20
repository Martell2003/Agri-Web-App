from app import create_app, db
from app.models.market import Market

# Create the Flask app and set up the app context
app = create_app()
app.app_context().push()

def update_market_coordinates():
    try:
        # Fetch markets
        nairobi_supermarkets = Market.query.filter_by(name="Nairobi Supermarkets").first()
        cheptulu = Market.query.filter_by(name="Cheptulu").first()
        kakamega_town = Market.query.filter_by(name="Kakamega Town").first()

        # Update coordinates
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

        # Commit changes
        db.session.commit()
        print("Market coordinates updated successfully!")

    except Exception as e:
        print(f"Error updating coordinates: {e}")
        db.session.rollback()

if __name__ == "__main__":
    update_market_coordinates()