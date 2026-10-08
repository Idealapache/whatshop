from flask import Flask, render_template
from models import db, Product
import os
from flask import Flask
from models import db
from routes import main

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///diva.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key")
app.config["ADMIN_PASSWORD"] = os.environ.get("ADMIN_PASSWORD", "diva-muse-admin")

# Diva Muse WhatsApp for booking notifications
app.config["WHATSAPP_NUMBER"] = "2348128992692"
app.config["BUSINESS_NAME"] = "Diva Muse Rentals"

UPLOAD_DIR = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

db.init_app(app)

with app.app_context():
    db.create_all()

    # Auto-create the Packages category if it doesn't exist
    from models import Category
    if not Category.query.filter_by(slug="packages").first():
        db.session.add(Category(name="Packages", slug="packages", sort_order=99))
        db.session.commit()

app.register_blueprint(main)

if __name__ == "__main__":
    app.run(debug=True)