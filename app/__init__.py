from datetime import datetime
from flask import Flask, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from config import Config
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin, BaseView, expose
import csv
from io import StringIO
from wtforms import SelectField, validators
import logging
from app.extensions import db

# Set up logging to both console and file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'debug.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize extensions directly
login_manager = LoginManager()
migrate = Migrate()
admin = Admin(name='AgriPriceTracker Admin', template_mode='bootstrap4')

# Custom Admin View with access control
class AdminModelView(ModelView):
    def is_accessible(self):
        logger.debug(f"Checking access for AdminModelView, user: {current_user}, is_admin: {current_user.is_admin if current_user.is_authenticated else False}")
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        logger.debug("AdminModelView inaccessible, redirecting to login")
        return redirect(url_for('auth.login'))

# Custom Market Admin View
class MarketModelView(ModelView):
    def is_accessible(self):
        logger.debug(f"Checking access for MarketModelView, user: {current_user}, is_admin: {current_user.is_admin if current_user.is_authenticated else False}")
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        logger.debug("MarketModelView inaccessible, redirecting to login")
        return redirect(url_for('auth.login'))

    # Customize the form
    form_args = {
        'name': {
            'label': 'Name',
            'validators': [validators.DataRequired()],
            'description': 'Enter the market name (e.g., Kibuye Market).'
        },
        'region_id': {
            'label': 'Region',
            'validators': [validators.DataRequired()],
            'description': 'Select the region where the market is located.'
        },
        'latitude': {
            'validators': [validators.Optional(), validators.NumberRange(min=-90, max=90, message="Latitude must be between -90 and 90")],
            'description': 'Enter latitude (e.g., -0.074 for Kisumu). Optional.'
        },
        'longitude': {
            'validators': [validators.Optional(), validators.NumberRange(min=-180, max=180, message="Longitude must be between -180 and 180")],
            'description': 'Enter longitude (e.g., 34.7778 for Kisumu). Optional.'
        }
    }

    # Specify which fields to show in the form and table
    form_columns = ['name', 'region_id', 'latitude', 'longitude']
    column_list = ['name', 'region', 'latitude', 'longitude']

    # Customize the region_id field’s choices
    def scaffold_form(self):
        form_class = super(MarketModelView, self).scaffold_form()
        form_class.region_id = SelectField('Region', coerce=int, validators=[validators.DataRequired()])
        return form_class

    # Set choices during form creation
    def create_form(self):
        from app.models.region import Region
        form = super(MarketModelView, self).create_form()
        form.region_id.choices = [(r.id, r.name) for r in Region.query.all()]
        return form

    def edit_form(self):
        from app.models.region import Region
        form = super(MarketModelView, self).edit_form()
        form.region_id.choices = [(r.id, r.name) for r in Region.query.all()]
        return form

# Custom CSV Upload View
class CSVUploadView(BaseView):
    def is_accessible(self):
        logger.debug(f"Checking access for CSVUploadView, user: {current_user}, is_admin: {current_user.is_admin if current_user.is_authenticated else False}")
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        logger.debug("CSVUploadView inaccessible, redirecting to login")
        return redirect(url_for('auth.login'))

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        logger.debug("Rendering CSVUploadView index")
        if request.method == 'POST':
            if 'csv_file' not in request.files:
                flash('No file part in the request.', 'danger')
                return self.render('admin/csv_upload.html')

            file = request.files['csv_file']
            if file.filename == '':
                flash('No file selected.', 'danger')
                return self.render('admin/csv_upload.html')

            if file and file.filename.endswith('.csv'):
                try:
                    # Read the CSV file
                    stream = StringIO(file.stream.read().decode('utf-8'), newline=None)
                    csv_reader = csv.DictReader(stream)

                    # Validate required columns
                    required_columns = ['product_name', 'market_name', 'price', 'timestamp']
                    if not all(col in csv_reader.fieldnames for col in required_columns):
                        flash(f'CSV file must contain the following columns: {", ".join(required_columns)}', 'danger')
                        return self.render('admin/csv_upload.html')

                    from app.models.product import Product
                    from app.models.market import Market
                    from app.models.price import Price

                    # Process each row
                    for row in csv_reader:
                        # Find the product
                        product = Product.query.filter_by(name=row['product_name']).first()
                        if not product:
                            flash(f"Product '{row['product_name']}' not found in the database.", 'danger')
                            continue

                        # Find the market
                        market = Market.query.filter_by(name=row['market_name']).first()
                        if not market:
                            flash(f"Market '{row['market_name']}' not found in the database.", 'danger')
                            continue

                        # Validate price and timestamp
                        try:
                            price_value = float(row['price'])
                            timestamp = datetime.strptime(row['timestamp'], '%Y-%m-%d')  # Fixed: Parse timestamp as datetime
                        except ValueError:
                            flash(f"Invalid price or timestamp in row: {row}", 'danger')
                            continue

                        # Create a new Price entry
                        new_price = Price(
                            product_id=product.id,
                            market_id=market.id,
                            price=price_value,
                            timestamp=timestamp
                        )
                        db.session.add(new_price)

                    # Commit the changes
                    db.session.commit()
                    flash('CSV file successfully uploaded and data imported!', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error processing CSV file: {str(e)}', 'danger')
            else:
                flash('Please upload a valid CSV file.', 'danger')

        return self.render('admin/csv_upload.html')

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    migrate.init_app(app, db)

    # Initialize Flask-Admin
    admin.init_app(app)

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.data import data_bp
    from app.routes.analysis import analysis_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(analysis_bp)

    # Define the user_loader function
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))

    # Add views to Flask-Admin
    from app.models.region import Region
    from app.models.market import Market
    from app.models.product import Product
    from app.models.price import Price
    from app.models.user import User

    admin.add_view(AdminModelView(Region, db.session, name='Region', endpoint='region'))
    admin.add_view(MarketModelView(Market, db.session, name='Market', endpoint='market'))
    admin.add_view(AdminModelView(Product, db.session, name='Product', endpoint='product'))
    admin.add_view(AdminModelView(Price, db.session, name='Price', endpoint='price'))
    admin.add_view(AdminModelView(User, db.session, name='User', endpoint='user'))
    admin.add_view(CSVUploadView(name='Upload CSV', endpoint='upload_csv'))

    return app