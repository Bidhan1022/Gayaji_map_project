# create_db.py

# app.py se 'app' variable ko import karo
from app import app 
# models.py se 'db' object aur apne Models (User, LocationPin) ko import karo
from models import db, User, LocationPin

print("Configuration check:")
print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

print("Database create karna shuru kar raha hoon...")

# App ka context zaroori hai
with app.app_context():
    # Yeh line aapke models.py mein define kiye gaye 
    # User aur LocationPin tables ko bana degi.
    db.create_all()

print("Database 'gaya_map.db' safalta-poorvak ban gaya hai!")