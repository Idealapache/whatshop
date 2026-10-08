from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0)


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship("Category")


class Booking(db.Model):
    __tablename__ = "bookings"
    id = db.Column(db.Integer, primary_key=True)

    client_name = db.Column(db.String(200), nullable=False)
    client_phone = db.Column(db.String(30), nullable=False)
    client_whatsapp = db.Column(db.String(30))
    client_email = db.Column(db.String(200))

    event_type = db.Column(db.String(100))
    event_date = db.Column(db.String(20))
    event_time = db.Column(db.String(20))
    guest_count = db.Column(db.Integer)

    venue = db.Column(db.String(255))
    address = db.Column(db.Text)
    area = db.Column(db.String(100))
    landmark = db.Column(db.String(255))

    needs_delivery = db.Column(db.Boolean, default=False)
    needs_setup = db.Column(db.Boolean, default=False)
    needs_pickup = db.Column(db.Boolean, default=False)
    own_transport = db.Column(db.Boolean, default=False)
    needs_logistics = db.Column(db.Boolean, default=False)

    items_summary = db.Column(db.Text, nullable=False)
    estimated_total = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)

    status = db.Column(db.String(20), default="new")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)