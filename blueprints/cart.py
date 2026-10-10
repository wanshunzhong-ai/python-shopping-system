"""购物车：加入、修改数量、删除、清空"""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from models import CartItem, Product

cart_bp = Blueprint("cart", __name__)


def _wants_json():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


@cart_bp.route("/")
@login_required
def view_cart():
    items = (
        current_user.cart_items.order_by(CartItem.created_at.desc()).all()
    )
    total = sum(i.subtotal for i in items)
    return render_template("cart.html", items=items, total=total)


@cart_bp.route("/add/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    product = db.session.get(Product, product_id)
    if not product or not product.is_active:
        if _wants_json():
            return jsonify(ok=False, msg="商品不存在"), 404
        flash("商品不存在", "danger")
        return redirect(url_for("shop.index"))

    qty = request.form.get("quantity", 1, type=int) or 1
    qty = max(1, qty)

    if product.stock <= 0:
        if _wants_json():
            return jsonify(ok=False, msg="该商品已售罄")
        flash("该商品已售罄", "warning")
        return redirect(url_for("shop.product_detail", product_id=product_id))

    item = CartItem.query.filter_by(
        user_id=current_user.id, product_id=product.id
    ).first()

    if item:
        new_qty = item.quantity + qty
    else:
        new_qty = qty

    if new_qty > product.stock:
        new_qty = product.stock
        msg = f"库存不足，已调整为 {product.stock} 件"
    else:
        msg = "已加入购物车"

    if item:
        item.quantity = new_qty
    else:
        db.session.add(
            CartItem(user_id=current_user.id, product_id=product.id, quantity=new_qty)
        )
    db.session.commit()

    if _wants_json():
        return jsonify(ok=True, msg=msg, cart_count=current_user.cart_count)

    # 立即购买：直接进入结算
    if request.form.get("buy_now"):
        return redirect(url_for("order.checkout"))

    flash(msg, "success")
    return redirect(request.form.get("next") or url_for("shop.product_detail", product_id=product_id))


@cart_bp.route("/update/<int:item_id>", methods=["POST"])
@login_required
def update_item(item_id):
    item = db.session.get(CartItem, item_id)
    if not item or item.user_id != current_user.id:
        flash("购物车条目不存在", "danger")
        return redirect(url_for("cart.view_cart"))

    qty = request.form.get("quantity", 1, type=int) or 1
    qty = max(1, qty)

    if qty > item.product.stock:
        qty = item.product.stock
        flash(f"库存不足，已调整为 {item.product.stock} 件", "warning")
    else:
        flash("数量已更新", "success")

    if qty <= 0:
        db.session.delete(item)
    else:
        item.quantity = qty
    db.session.commit()
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_item(item_id):
    item = db.session.get(CartItem, item_id)
    if item and item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
        flash("已移出购物车", "success")
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/clear", methods=["POST"])
@login_required
def clear_cart():
    current_user.cart_items.delete()
    db.session.commit()
    flash("购物车已清空", "success")
    return redirect(url_for("cart.view_cart"))
