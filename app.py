from flask import Flask, render_template
from models import db, Product
from urllib.parse import quote
from flask import request, jsonify
from models import db, Product, Order
from flask import request, session, redirect, url_for
from functools import wraps
import os
import uuid
from werkzeug.utils import secure_filename
from flask import send_from_directory

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///shop.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["WHATSAPP_NUMBER"] = "2348128992692"  # replace with the client's number
app.config["SECRET_KEY"] = "dev-secret-change-me"
app.config["ADMIN_PASSWORD"] = "diva-muse"

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper

UPLOAD_DIR = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

db.init_app(app)


with app.app_context():
    db.create_all()

@app.route("/")
def home():
    products = Product.query.all()
    return render_template("index.html", products=products)

@app.route("/product/<int:pid>")
def product(pid):
    p = Product.query.get_or_404(pid)
    return render_template("product.html", product=p)

@app.route("/cart")
def cart():
    return render_template("cart.html")

@app.route("/checkout", methods=["POST"])
def checkout():
    data = request.get_json()
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    items = data.get("items") or []

    if not name or not phone or not items:
        return jsonify({"error": "Missing fields"}), 400

    lines = []
    total = 0
    for item in items:
        p = Product.query.get(item["id"])
        if not p:
            continue
        qty = int(item.get("qty", 1))
        subtotal = p.price * qty
        total += subtotal
        lines.append(f"• {p.name} x{qty} — ₦{subtotal:,}")

    summary = "\n".join(lines)

    order = Order(
        customer_name=name,
        customer_phone=phone,
        items_summary=summary,
        total=total,
    )
    db.session.add(order)
    db.session.commit()

    msg = (
        f"New order from {name}\n"
        f"Phone: {phone}\n\n"
        f"{summary}\n\n"
        f"Total: ₦{total:,}"
    )
    wa_link = f"https://wa.me/{app.config['WHATSAPP_NUMBER']}?text={quote(msg)}"

    return jsonify({"whatsapp": wa_link, "order_id": order.id})

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == app.config["ADMIN_PASSWORD"]:
            session["admin"] = True
            return redirect(url_for("admin_products"))
        return render_template("admin_login.html", error="Wrong password")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_products():
    products = Product.query.all()
    return render_template("admin_products.html", products=products)


@app.route("/admin/products/new", methods=["GET", "POST"])
@admin_required
def admin_product_new():
    if request.method == "POST":
        p = Product(
            name=request.form["name"],
            description=request.form.get("description", "").strip() or None,
            price=int(request.form.get("price") or 0),
        )

        file = request.files.get("image")
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            file.save(os.path.join(UPLOAD_DIR, filename))
            p.image = filename

        db.session.add(p)
        db.session.commit()
        return redirect(url_for("admin_products"))
    return render_template("admin_form.html", product=None)


@app.route("/admin/products/<int:pid>/edit", methods=["GET", "POST"])
@admin_required
def admin_product_edit(pid):
    p = Product.query.get_or_404(pid)
    if request.method == "POST":
        p.name = request.form["name"]
        p.price = int(request.form.get("price") or 0)
        p.description = request.form.get("description", "").strip() or None

        file = request.files.get("image")
        if file and file.filename and allowed_file(file.filename):
            # Delete the old image if it exists
            if p.image:
                old = os.path.join(UPLOAD_DIR, p.image)
                if os.path.exists(old):
                    os.remove(old)

            ext = file.filename.rsplit(".", 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            file.save(os.path.join(UPLOAD_DIR, filename))
            p.image = filename

        db.session.commit()
        return redirect(url_for("admin_products"))
    return render_template("admin_form.html", product=p)

@app.route("/admin/products/<int:pid>/delete", methods=["POST"])
@admin_required
def admin_product_delete(pid):
    p = Product.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    return redirect(url_for("admin_products"))

if __name__ == "__main__":
    app.run(debug=True)