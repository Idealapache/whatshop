import os
import uuid
from functools import wraps
from urllib.parse import quote
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, current_app, jsonify
)
from models import db, Category, Product, Booking

main = Blueprint("main", __name__)


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("main.admin_login"))
        return f(*args, **kwargs)
    return wrapper


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {
        "png", "jpg", "jpeg", "webp", "gif"
    }


# ---------------- PUBLIC ----------------

@main.route("/")
def home():
    return render_template("index.html")


@main.route("/shop")
def shop():
    categories = Category.query.order_by(Category.sort_order).all()
    result = []
    for c in categories:
        products = Product.query.filter_by(category_id=c.id, active=True).all()
        if products:
            result.append({"category": c, "products": products})
    return render_template("shop.html", groups=result)


@main.route("/events")
def events():
    event = request.args.get("event", "").strip()
    guests = request.args.get("guests", "").strip()

    packages_cat = Category.query.filter_by(slug="packages").first()
    packages = []
    if packages_cat:
        packages = Product.query.filter_by(category_id=packages_cat.id, active=True).all()

    # Filter by name — only if the user actually picked something
    if event or guests:
        filtered = []
        for p in packages:
            name_lower = p.name.lower()
            if event and event.lower() not in name_lower:
                continue
            if guests and guests not in p.name:
                continue
            filtered.append(p)
        packages = filtered  # no fallback — show what matches, even if empty

    return render_template("events.html", packages=packages, event=event, guests=guests)


@main.route("/product/<int:pid>")
def product(pid):
    p = Product.query.get_or_404(pid)
    return render_template("product.html", product=p)


@main.route("/selection")
def selection():
    return render_template("selection.html")


@main.route("/book", methods=["GET", "POST"])
def book():
    if request.method == "POST":
        items_json = request.form.get("items", "[]")
        import json
        try:
            items = json.loads(items_json)
        except Exception:
            items = []

        if not items:
            return redirect(url_for("main.selection"))

        lines = []
        total = 0
        for item in items:
            p = Product.query.get(item.get("id"))
            if not p:
                continue
            qty = int(item.get("qty", 1))
            subtotal = p.price * qty
            total += subtotal
            lines.append(f"• {p.name} x{qty} — ₦{subtotal:,}")

        summary = "\n".join(lines)

        booking = Booking(
            client_name=request.form["client_name"],
            client_phone=request.form["client_phone"],
            client_whatsapp=request.form.get("client_whatsapp"),
            client_email=request.form.get("client_email"),
            event_type=request.form.get("event_type"),
            event_date=request.form.get("event_date"),
            event_time=request.form.get("event_time"),
            guest_count=int(request.form.get("guest_count") or 0) or None,
            venue=request.form.get("venue"),
            address=request.form.get("address"),
            area=request.form.get("area"),
            landmark=request.form.get("landmark"),
            needs_delivery="needs_delivery" in request.form,
            needs_setup="needs_setup" in request.form,
            needs_pickup="needs_pickup" in request.form,
            own_transport="own_transport" in request.form,
            needs_logistics="needs_logistics" in request.form,
            items_summary=summary,
            estimated_total=total,
            notes=request.form.get("notes"),
        )
        db.session.add(booking)
        db.session.commit()

        # Build WhatsApp message
        services = []
        if booking.needs_delivery: services.append("Delivery")
        if booking.needs_setup: services.append("Setup")
        if booking.needs_pickup: services.append("Pickup")
        if booking.own_transport: services.append("Own transport")
        if booking.needs_logistics: services.append("Needs logistics help")

        msg = (
            f"NEW BOOKING REQUEST\n\n"
            f"Name: {booking.client_name}\n"
            f"Phone: {booking.client_phone}\n"
            f"WhatsApp: {booking.client_whatsapp or '—'}\n"
            f"Email: {booking.client_email or '—'}\n\n"
            f"EVENT\n"
            f"Type: {booking.event_type or '—'}\n"
            f"Date: {booking.event_date or '—'}\n"
            f"Time: {booking.event_time or '—'}\n"
            f"Guests: {booking.guest_count or '—'}\n\n"
            f"LOCATION\n"
            f"Venue: {booking.venue or '—'}\n"
            f"Address: {booking.address or '—'}\n"
            f"Area: {booking.area or '—'}\n"
            f"Landmark: {booking.landmark or '—'}\n\n"
            f"SERVICES\n"
            f"{', '.join(services) if services else '—'}\n\n"
            f"SELECTION\n{summary}\n\n"
            f"ESTIMATED TOTAL: ₦{total:,}\n\n"
            f"NOTES: {booking.notes or '—'}"
        )

        wa = f"https://wa.me/{current_app.config['WHATSAPP_NUMBER']}?text={quote(msg)}"

        return render_template("booking_confirmed.html", booking=booking, wa=wa)

    return render_template("book.html")


# ---------------- ADMIN ----------------

@main.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == current_app.config["ADMIN_PASSWORD"]:
            session["admin"] = True
            return redirect(url_for("main.admin_home"))
        return render_template("admin_login.html", error="Wrong password")
    return render_template("admin_login.html")


@main.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("main.admin_login"))


@main.route("/admin")
@admin_required
def admin_home():
    counts = {
        "products": Product.query.count(),
        "categories": Category.query.count(),
        "bookings": Booking.query.count(),
        "new_bookings": Booking.query.filter_by(status="new").count(),
    }
    return render_template("admin_home.html", counts=counts)


# ---- Categories ----

@main.route("/admin/categories")
@admin_required
def admin_categories():
    items = Category.query.order_by(Category.sort_order).all()
    return render_template("admin_categories.html", categories=items)


@main.route("/admin/categories/new", methods=["GET", "POST"])
@admin_required
def admin_category_new():
    if request.method == "POST":
        c = Category(
            name=request.form["name"],
            slug=request.form["slug"],
            sort_order=int(request.form.get("sort_order") or 0),
        )
        db.session.add(c)
        db.session.commit()
        return redirect(url_for("main.admin_categories"))
    return render_template("admin_category_form.html", category=None)


@main.route("/admin/categories/<int:cid>/edit", methods=["GET", "POST"])
@admin_required
def admin_category_edit(cid):
    c = Category.query.get_or_404(cid)
    if request.method == "POST":
        c.name = request.form["name"]
        c.slug = request.form["slug"]
        c.sort_order = int(request.form.get("sort_order") or 0)
        db.session.commit()
        return redirect(url_for("main.admin_categories"))
    return render_template("admin_category_form.html", category=c)


@main.route("/admin/categories/<int:cid>/delete", methods=["POST"])
@admin_required
def admin_category_delete(cid):
    c = Category.query.get_or_404(cid)
    Product.query.filter_by(category_id=cid).update({"category_id": None})
    db.session.delete(c)
    db.session.commit()
    return redirect(url_for("main.admin_categories"))


# ---- Products ----

@main.route("/admin/products")
@admin_required
def admin_products():
    items = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("admin_products.html", products=items)


@main.route("/admin/products/new", methods=["GET", "POST"])
@admin_required
def admin_product_new():
    categories = Category.query.order_by(Category.sort_order).all()
    if request.method == "POST":
        p = Product(
            name=request.form["name"],
            description=request.form.get("description"),
            price=int(request.form.get("price") or 0),
            category_id=request.form.get("category_id") or None,
            active="active" in request.form,
        )
        file = request.files.get("image")
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            file.save(os.path.join(current_app.root_path, "static", "uploads", filename))
            p.image = filename
        db.session.add(p)
        db.session.commit()
        return redirect(url_for("main.admin_products"))
    return render_template("admin_product_form.html", product=None, categories=categories)


@main.route("/admin/products/<int:pid>/edit", methods=["GET", "POST"])
@admin_required
def admin_product_edit(pid):
    p = Product.query.get_or_404(pid)
    categories = Category.query.order_by(Category.sort_order).all()
    if request.method == "POST":
        p.name = request.form["name"]
        p.description = request.form.get("description")
        p.price = int(request.form.get("price") or 0)
        p.category_id = request.form.get("category_id") or None
        p.active = "active" in request.form
        file = request.files.get("image")
        if file and file.filename and allowed_file(file.filename):
            old = os.path.join(current_app.root_path, "static", "uploads", p.image or "")
            if p.image and os.path.exists(old):
                os.remove(old)
            ext = file.filename.rsplit(".", 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            file.save(os.path.join(current_app.root_path, "static", "uploads", filename))
            p.image = filename
        db.session.commit()
        return redirect(url_for("main.admin_products"))
    return render_template("admin_product_form.html", product=p, categories=categories)


@main.route("/admin/products/<int:pid>/delete", methods=["POST"])
@admin_required
def admin_product_delete(pid):
    p = Product.query.get_or_404(pid)
    if p.image:
        old = os.path.join(current_app.root_path, "static", "uploads", p.image)
        if os.path.exists(old):
            os.remove(old)
    db.session.delete(p)
    db.session.commit()
    return redirect(url_for("main.admin_products"))


# ---- Bookings ----

@main.route("/admin/bookings")
@admin_required
def admin_bookings():
    items = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template("admin_bookings.html", bookings=items)


@main.route("/admin/bookings/<int:bid>/status/<status>", methods=["POST"])
@admin_required
def admin_booking_status(bid, status):
    b = Booking.query.get_or_404(bid)
    if status in ("new", "reviewed", "invoiced", "paid", "cancelled"):
        b.status = status
        db.session.commit()
    return redirect(url_for("main.admin_bookings"))


@main.route("/admin/bookings/<int:bid>/delete", methods=["POST"])
@admin_required
def admin_booking_delete(bid):
    b = Booking.query.get_or_404(bid)
    db.session.delete(b)
    db.session.commit()
    return redirect(url_for("main.admin_bookings"))