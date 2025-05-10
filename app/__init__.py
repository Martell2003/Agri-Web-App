from datetime import datetime
from flask import Flask, redirect, url_for, request, flash, render_template
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from config import Config
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, validators
from werkzeug.security import generate_password_hash
import logging
from app.extensions import db
import csv
from io import StringIO

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'debug.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize extensions
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    migrate.init_app(app, db)

    # Custom Admin Index View with Dashboard
    class CustomAdminIndexView(AdminIndexView):
        @expose('/')
        def index(self):
            if not current_user.is_authenticated or not current_user.is_admin:
                flash('Admin access required.', 'danger')
                return redirect(url_for('auth.login'))

            # Calculate record counts for dashboard
            from app.models.user import User
            from app.models.region import Region
            from app.models.market import Market
            from app.models.product import Product
            from app.models.price import Price
            
            record_counts = {
                'users': User.query.count(),
                'regions': Region.query.count(),
                'markets': Market.query.count(),
                'products': Product.query.count(),
                'prices': Price.query.count()
            }
            return self.render('admin/dashboard.html', record_counts=record_counts)

    # Initialize Flask-Admin
    admin = Admin(
        app,
        name='AgriPrice Tracker Admin',
        template_mode='bootstrap4',
        index_view=CustomAdminIndexView()
    )

    # Base Admin Model View
    class SecureModelView(ModelView):
        def is_accessible(self):
            return current_user.is_authenticated and current_user.is_admin

        def inaccessible_callback(self, name, **kwargs):
            return redirect(url_for('auth.login'))

    # User Admin Form
    class UserAdminForm(FlaskForm):
        username = StringField('Username', validators=[validators.DataRequired()])
        email = StringField('Email', validators=[validators.DataRequired(), validators.Email()])
        password = PasswordField('Password', validators=[validators.Optional()])
        is_admin = BooleanField('Is Admin')

    # User Model View
    class UserModelView(SecureModelView):
        form = UserAdminForm
        column_list = ['id', 'username', 'email', 'is_admin']
        form_columns = ['username', 'email', 'password', 'is_admin']
        column_filters = ['username', 'email']
        column_searchable_list = ['username', 'email']

        def on_model_change(self, form, model, is_created):
            if form.password.data:
                model.password_hash = generate_password_hash(form.password.data)
            elif is_created and not form.password.data:
                raise ValueError('Password is required for new users.')

    # Product Model View
    class ProductModelView(SecureModelView):
        column_list = ['id', 'name']
        form_columns = ['name']
        column_filters = ['name']
        column_searchable_list = ['name']
        form_args = {
            'name': {'validators': [validators.DataRequired()]}
        }

    # Price Model View
    class PriceModelView(SecureModelView):
        column_list = ['id', 'product.name', 'market.name', 'price', 'timestamp']
        form_columns = ['product_id', 'market_id', 'price', 'timestamp']
        column_filters = ['price', 'timestamp']
        column_searchable_list = ['price']
        form_args = {
            'price': {'validators': [validators.DataRequired(), validators.NumberRange(min=0)]},
            'timestamp': {'validators': [validators.DataRequired()]}
        }

        def scaffold_form(self):
            form_class = super().scaffold_form()
            from app.models.product import Product
            from app.models.market import Market
            form_class.product_id = SelectField('Product', coerce=int, validators=[validators.DataRequired()])
            form_class.market_id = SelectField('Market', coerce=int, validators=[validators.DataRequired()])
            return form_class

        def create_form(self):
            form = super().create_form()
            from app.models.product import Product
            from app.models.market import Market
            form.product_id.choices = [(p.id, p.name) for p in Product.query.order_by(Product.name).all()]
            form.market_id.choices = [(m.id, m.name) for m in Market.query.order_by(Market.name).all()]
            return form

        def edit_form(self):
            form = super().edit_form()
            from app.models.product import Product
            from app.models.market import Market
            form.product_id.choices = [(p.id, p.name) for p in Product.query.order_by(Product.name).all()]
            form.market_id.choices = [(m.id, m.name) for m in Market.query.order_by(Market.name).all()]
            return form

    # Market Model View
    class MarketModelView(SecureModelView):
        column_list = ['id', 'name', 'region.name', 'latitude', 'longitude']
        form_columns = ['name', 'region_id', 'latitude', 'longitude']
        column_filters = ['name']
        form_args = {
            'name': {'validators': [validators.DataRequired()]},
            'latitude': {'validators': [validators.Optional(), validators.NumberRange(min=-90, max=90)]},
            'longitude': {'validators': [validators.Optional(), validators.NumberRange(min=-180, max=180)]}
        }

        def scaffold_form(self):
            form_class = super().scaffold_form()
            from app.models.region import Region
            form_class.region_id = SelectField('Region', coerce=int, validators=[validators.DataRequired()])
            return form_class

        def create_form(self):
            form = super().create_form()
            from app.models.region import Region
            form.region_id.choices = [(r.id, r.name) for r in Region.query.order_by(Region.name).all()]
            return form

        def edit_form(self):
            form = super().edit_form()
            from app.models.region import Region
            form.region_id.choices = [(r.id, r.name) for r in Region.query.order_by(Region.name).all()]
            return form

    # CSV Upload View
    class CSVUploadView(BaseView):
        @expose('/', methods=['GET', 'POST'])
        def index(self):
            if not current_user.is_authenticated or not current_user.is_admin:
                flash('Admin access required.', 'danger')
                return redirect(url_for('auth.login'))

            if request.method == 'POST':
                if 'csv_file' not in request.files:
                    flash('No file uploaded.', 'danger')
                    return self.render('admin/csv_upload.html')

                file = request.files['csv_file']
                if file.filename == '' or not file.filename.endswith('.csv'):
                    flash('Please upload a valid CSV file.', 'danger')
                    return self.render('admin/csv_upload.html')

                try:
                    stream = StringIO(file.stream.read().decode('utf-8'))
                    csv_reader = csv.DictReader(stream)
                    required_columns = ['product_name', 'market_name', 'price', 'timestamp']
                    if not all(col in csv_reader.fieldnames for col in required_columns):
                        flash(f'CSV must include: {", ".join(required_columns)}', 'danger')
                        return self.render('admin/csv_upload.html')

                    from app.models.product import Product
                    from app.models.market import Market
                    from app.models.price import Price

                    for row in csv_reader:
                        product = Product.query.filter_by(name=row['product_name']).first()
                        market = Market.query.filter_by(name=row['market_name']).first()
                        if not product or not market:
                            flash(f"Invalid product ({row['product_name']}) or market ({row['market_name']})", 'danger')
                            continue
                        try:
                            price = float(row['price'])
                            timestamp = datetime.strptime(row['timestamp'], '%Y-%m-%d')
                        except ValueError:
                            flash(f"Invalid price or timestamp in row: {row}", 'danger')
                            continue

                        price_record = Price(
                            product_id=product.id,
                            market_id=market.id,
                            price=price,
                            timestamp=timestamp
                        )
                        db.session.add(price_record)

                    db.session.commit()
                    flash('CSV data imported successfully!', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error importing CSV: {str(e)}', 'danger')

            return self.render('admin/csv_upload.html')

    # Register Admin Views
    from app.models.user import User
    from app.models.region import Region
    from app.models.market import Market
    from app.models.product import Product
    from app.models.price import Price

    admin.add_view(UserModelView(User, db.session, name='Users'))
    admin.add_view(SecureModelView(Region, db.session, name='Regions'))
    admin.add_view(MarketModelView(Market, db.session, name='Markets'))
    admin.add_view(ProductModelView(Product, db.session, name='Products'))
    admin.add_view(PriceModelView(Price, db.session, name='Prices'))
    admin.add_view(CSVUploadView(name='Upload CSV', endpoint='csv_upload'))

    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.data import data_bp
    from app.routes.analysis import analysis_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(analysis_bp)

    # User Loader
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))

    return app