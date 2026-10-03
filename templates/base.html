from functools import wraps
from urllib.parse import quote
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, current_app, jsonify
)
from models import db, Product, Order

main = Blueprint("main", __name__)


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("main.admin_login"))
        return f(*args, **kwargs)
    return wrapper


# ---------------- PUBLIC ----------------

@main.route("/")
def home():
    products = Product.query.filter_by(active=True).order_by(Product.created_at.desc()).all()
    return render_template("index.html", products=products)


@main.route("/product/<int:pid>")
def product(pid):
    p = Product.query.get_or_404(pid)
    return render_template("product.html", product=p)


@main.route("/cart")
def cart():
    return render_template("cart.html")


@main.route("/checkout", methods=["POST"])
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
    wa_link = f"https://wa.me/{current_app.config['WHATSAPP_NUMBER']}?text={quote(msg)}"

    return jsonify({"whatsapp": wa_link, "order_id": order.id})


# ---------------- ADMIN ----------------

@main.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == current_app.config["ADMIN_PASSWORD"]:
            session["admin"] = True
            return redirect(url_for("main.admin_products"))
        return render_template("admin_login.html", error="Wrong password")
    return render_template("admin_login.html")


@main.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("main.admin_login"))


@main.route("/admin")
@admin_required
def admin_products():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("admin_products.html", products=products)


@main.route("/admin/products/new", methods=["GET", "POST"])
@admin_required
def admin_product_new():
    if request.method == "POST":
        p = Product(
            name=request.form["name"],
            description=request.form.get("description"),
            price=int(request.form.get("price") or 0),
            image_url=request.form.get("image_url"),
            active="active" in request.form,
        )
        db.session.add(p)
        db.session.commit()
        return redirect(url_for("main.admin_products"))
    return render_template("admin_form.html", product=None)


@main.route("/admin/products/<int:pid>/edit", methods=["GET", "POST"])
@admin_required
def admin_product_edit(pid):
    p = Product.query.get_or_404(pid)
    if request.method == "POST":
        p.name = request.form["name"]
        p.description = request.form.get("description")
        p.price = int(request.form.get("price") or 0)
        p.image_url = request.form.get("image_url")
        p.active = "active" in request.form
        db.session.commit()
        return redirect(url_for("main.admin_products"))
    return render_template("admin_form.html", product=p)


@main.route("/admin/products/<int:pid>/delete", methods=["POST"])
@admin_required
def admin_product_delete(pid):
    p = Product.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    return redirect(url_for("main.admin_products"))


@main.route("/admin/orders")
@admin_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin_orders.html", orders=orders)


@main.route("/admin/orders/<int:oid>/status/<status>", methods=["POST"])
@admin_required
def admin_order_status(oid, status):
    o = Order.query.get_or_404(oid)
    if status in ("new", "paid", "delivered", "cancelled"):
        o.status = status
        db.session.commit()
    return redirect(url_for("main.admin_orders"))