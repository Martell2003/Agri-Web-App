from app import create_app, db
from sqlalchemy.sql import text

app = create_app()
app.app_context().push()

# Drop the user table
db.session.execute(text('DROP TABLE IF EXISTS user'))
db.session.commit()

# Recreate all tables
db.create_all()

print("User table dropped and recreated successfully.")