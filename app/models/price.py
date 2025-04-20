  
from app.extensions import db
from sqlalchemy import CheckConstraint
from datetime import datetime

#data validation and integrity

class Price(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    market_id = db.Column(db.Integer, db.ForeignKey('market.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

        # Relationships
    product = db.relationship('Product', backref='prices')
    market = db.relationship('Market', backref='prices')

    # Add a constraint to ensure prices are non-negative
    __table_args__ = (
        CheckConstraint('price >= 0', name='non_negative_price'),
    )

    def __repr__(self):
        return f'<Price {self.product_id} at {self.market_id}: {self.price}>'