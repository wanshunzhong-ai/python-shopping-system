"""订单：结算、创建订单、订单列表 / 详情、取消、确认收货"""
from flask import (
    Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
)
from flask_login import current_user, login_required

from extensions import db
from models import CartItem, Order, OrderItem, Product

order_bp = Blueprint("order", __name__)


@order_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    items = current_user.cart_items.order_by(CartItem.created_at.desc()).all()
    if not items:
        flash("购物车是空的，先去挑点好东西吧", "warning")
        return redirect(url_for("shop.index"))

    total = sum(i.subtotal for i in items)

    if request.method == "POST":
        receiver_name = (request.form.get("receiver_name") or "").strip()
        receiver_phone = (request.form.get("receiver_phone") or "").strip()
        receiver_address = (request.form.get("receiver_address") or "").strip()
        payment_method = request.form.get("payment_method") or "在线支付"
        remark = (request.form.get("remark") or "").strip()

        errors = []
        if not receiver_name:
            errors.append("请填写收货人姓名")
        if not receiver_phone:
            errors.append("请填写联系电话")
        if not receiver_address:
            errors.append("请填写收货地址")

        # 校验库存
        for it in items:
            if it.quantity > it.product.stock:
                errors.append(f"《{it.product.name}》库存不足，仅剩 {it.product.stock} 件")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("checkout.html", items=items, total=total)

        # 创建订单
        order = Order(
            order_no=Order.generate_order_no(),
            user_id=current_user.id,
            total_amount=total,
            receiver_name=receiver_name,
            receiver_phone=receiver_phone,
            receiver_address=receiver_address,
            payment_method=payment_method,
            remark=remark,
            status=Order.STATUS_PENDING,
        )
        db.session.add(order)
        db.session.flush()  # 拿到 order.id

        for it in items:
            db.session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=it.product_id,
                    product_name=it.product.name,
                    product_image=it.product.image,
                    price=it.product.price,
                    quantity=it.quantity,
                )
            )
            # 扣减库存、增加销量
            it.product.stock -= it.quantity
            it.product.sales += it.quantity

        # 清空购物车
        for it in items:
            db.session.delete(it)

        db.session.commit()
        flash("下单成功！", "success")
        return redirect(url_for("order.detail", order_id=order.id))

    return render_template("checkout.html", items=items, total=total)


@order_bp.route("/list")
@login_required
def order_list():
    status = request.args.get("status")
    page = request.args.get("page", 1, type=int)

    query = current_user.orders
    if status in dict(Order.STATUS_MAP):
        query = query.filter(Order.status == status)

    pagination = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=current_app.config["ORDERS_PER_PAGE"], error_out=False
    )
    return render_template(
        "orders.html",
        pagination=pagination,
        orders=pagination.items,
        current_status=status,
        status_map=Order.STATUS_MAP,
    )


@order_bp.route("/<int:order_id>")
@login_required
def detail(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)
    if order.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return render_template("order_detail.html", order=order)


@order_bp.route("/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)
    if order.user_id != current_user.id:
        abort(403)
    if order.status != Order.STATUS_PENDING:
        flash("该订单当前状态不可取消", "warning")
        return redirect(url_for("order.detail", order_id=order.id))

    order.status = Order.STATUS_CANCELED
    # 回滚库存与销量
    for it in order.items:
        product = db.session.get(Product, it.product_id) if it.product_id else None
        if product:
            product.stock += it.quantity
            product.sales = max(0, product.sales - it.quantity)
    db.session.commit()
    flash("订单已取消", "success")
    return redirect(url_for("order.detail", order_id=order.id))


@order_bp.route("/<int:order_id>/confirm", methods=["POST"])
@login_required
def confirm_receive(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)
    if order.user_id != current_user.id:
        abort(403)
    if order.status != Order.STATUS_SHIPPED:
        flash("该订单当前状态不可确认收货", "warning")
        return redirect(url_for("order.detail", order_id=order.id))

    order.status = Order.STATUS_DONE
    db.session.commit()
    flash("已确认收货，感谢您的购买！", "success")
    return redirect(url_for("order.detail", order_id=order.id))
