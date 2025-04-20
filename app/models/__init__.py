from app.extensions import db

# Import all models here
from .user import User
from .product import Product
from .price import Price
from .market import Market
from .region import Region


# Optional: Define a function to initialize models
def init_models(app):
    with app.app_context():
        db.create_all()