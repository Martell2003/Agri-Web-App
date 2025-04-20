from app import create_app, db
from app.models.user import User

app = create_app()
app.app_context().push()

def create_admin_user():
    # Check if the admin user already exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='adeyandubisimon@gmail.com', is_admin=True)
        admin.set_password('Turkhella_martell2003')  # Change this password!
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: username=admin, email=adeyandubisimon@gmail.com, password=Turkhella_martell2003")
    else:
        print("Admin user already exists")

if __name__ == "__main__":
    create_admin_user()