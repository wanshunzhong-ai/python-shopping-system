"""后台管理：仪表盘、商品、分类、订单、用户"""
import os
import uuid
from functools import wraps

from flask import (
    Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
)
from flask_login import current_user, login_required
from sqlalchemy import func
from werkzeug.utils import secure_filename

from extensions import db
from models import CartItem, Category, Order, OrderItem, Product, User

admin_bp = Blueprint("admin", __name__)


def admin_required(f):
    """仅管理员可访问"""

    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)

    return wrapper


@admin_bp.context_processor
def inject_admin_globals():
    return {"admin_section": request.endpoint}


# ---------------------------- 仪表盘 ----------------------------
@admin_bp.route("/")
@admin_required
def dashboard():
    # 基础统计
    stats = {
        "user_count": User.query.count(),
        "product_count": Product.query.count(),
        "category_count": Category.query.count(),
        "order_count": Order.query.count(),
        "total_sales": db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
        .filter(Order.status != Order.STATUS_CANCELED)
        .scalar(),
    }

    # 各状态订单数
    status_counts = dict(
        db.session.query(Order.status, func.count(Order.id))
        .group_by(Order.status)
        .all()
    )

    # 销量 Top 5
    top_products = (
        Product.query.order_by(Product.sales.desc()).limit(5).all()
    )
    # 最近订单
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(8).all()
    # 低库存预警
    low_stock = (
        Product.query.filter(Product.stock <= 10)
        .order_by(Product.stock.asc())
        .limit(8)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        status_counts=status_counts,
        top_products=top_products,
        recent_orders=recent_orders,
        low_stock=low_stock,
        status_map=Order.STATUS_MAP,
    )


# ---------------------------- 商品管理 ----------------------------
@admin_bp.route("/products")
@admin_required
def products():
    page = request.args.get("page", 1, type=int)
    keyword = (request.args.get("q") or "").strip()
    category_id = request.args.get("category", type=int)

    query = Product.query
    if keyword:
        query = query.filter(Product.name.like(f"%{keyword}%"))
    if category_id:
        query = query.filter(Product.category_id == category_id)

    pagination = query.order_by(Product.id.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    categories = Category.query.order_by(Category.sort_order).all()
    return render_template(
        "admin/products.html",
        pagination=pagination,
        products=pagination.items,
        categories=categories,
        keyword=keyword,
        current_category=category_id,
    )


def _save_image(file):
    """保存上传图片，返回相对 static 的路径"""
    if not file or not file.filename:
        return None
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in current_app.config["ALLOWED_EXTENSIONS"]:
        return None
    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
    return f"uploads/{filename}"


def _int_or(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _float_or(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@admin_bp.route("/product/new", methods=["GET", "POST"])
@admin_required
def product_create():
    categories = Category.query.order_by(Category.sort_order).all()
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("商品名称不能为空", "danger")
            return render_template(
                "admin/product_form.html", product=None, categories=categories
            )

        image = _save_image(request.files.get("image_file"))
        if not image:
            image = (request.form.get("image") or "").strip() or None

        product = Product(
            name=name,
            category_id=request.form.get("category_id", type=int),
            price=_float_or(request.form.get("price")),
            original_price=_float_or(request.form.get("original_price")) or None,
            stock=_int_or(request.form.get("stock")),
            image=image,
            summary=(request.form.get("summary") or "").strip(),
            description=(request.form.get("description") or "").strip(),
            is_active=bool(request.form.get("is_active")),
        )
        db.session.add(product)
        db.session.commit()
        flash("商品创建成功", "success")
        return redirect(url_for("admin.products"))

    return render_template(
        "admin/product_form.html", product=None, categories=categories
    )


@admin_bp.route("/product/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def product_edit(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)
    categories = Category.query.order_by(Category.sort_order).all()

    if request.method == "POST":
        product.name = (request.form.get("name") or "").strip() or product.name
        product.category_id = request.form.get("category_id", type=int)
        product.price = _float_or(request.form.get("price"), product.price)
        product.original_price = _float_or(request.form.get("original_price")) or None
        product.stock = _int_or(request.form.get("stock"), product.stock)
        product.summary = (request.form.get("summary") or "").strip()
        product.description = (request.form.get("description") or "").strip()
        product.is_active = bool(request.form.get("is_active"))

        new_image = _save_image(request.files.get("image_file"))
        if new_image:
            product.image = new_image
        elif (request.form.get("image") or "").strip():
            product.image = request.form.get("image").strip()

        db.session.commit()
        flash("商品已更新", "success")
        return redirect(url_for("admin.products"))

    return render_template(
        "admin/product_form.html", product=product, categories=categories
    )


@admin_bp.route("/product/<int:product_id>/delete", methods=["POST"])
@admin_required
def product_delete(product_id):
    product = db.session.get(Product, product_id)
    if product:
        CartItem.query.filter_by(product_id=product.id).delete()
        db.session.delete(product)
        db.session.commit()
        flash("商品已删除", "success")
    return redirect(url_for("admin.products"))


@admin_bp.route("/product/<int:product_id>/toggle", methods=["POST"])
@admin_required
def product_toggle(product_id):
    product = db.session.get(Product, product_id)
    if product:
        product.is_active = not product.is_active
        db.session.commit()
        flash("已上架" if product.is_active else "已下架", "success")
    return redirect(url_for("admin.products"))


# ---------------------------- 分类管理 ----------------------------
@admin_bp.route("/categories", methods=["GET", "POST"])
@admin_required
def categories():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("分类名称不能为空", "danger")
        elif Category.query.filter_by(name=name).first():
            flash("该分类已存在", "danger")
        else:
            db.session.add(
                Category(
                    name=name,
                    icon=(request.form.get("icon") or "📦").strip(),
                    description=(request.form.get("description") or "").strip(),
                    sort_order=_int_or(request.form.get("sort_order")),
                )
            )
            db.session.commit()
            flash("分类已添加", "success")
        return redirect(url_for("admin.categories"))

    cats = Category.query.order_by(Category.sort_order, Category.id).all()
    return render_template("admin/categories.html", categories=cats)


@admin_bp.route("/category/<int:category_id>/edit", methods=["POST"])
@admin_required
def category_edit(category_id):
    cat = db.session.get(Category, category_id)
    if cat:
        name = (request.form.get("name") or "").strip()
        if name:
            dup = Category.query.filter(Category.name == name, Category.id != cat.id).first()
            if dup:
                flash("该分类名称已存在", "danger")
                return redirect(url_for("admin.categories"))
            cat.name = name
        cat.icon = (request.form.get("icon") or cat.icon).strip()
        cat.description = (request.form.get("description") or "").strip()
        cat.sort_order = _int_or(request.form.get("sort_order"), cat.sort_order)
        db.session.commit()
        flash("分类已更新", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/category/<int:category_id>/delete", methods=["POST"])
@admin_required
def category_delete(category_id):
    cat = db.session.get(Category, category_id)
    if cat:
        if cat.products.count() > 0:
            flash("该分类下还有商品，无法删除", "warning")
        else:
            db.session.delete(cat)
            db.session.commit()
            flash("分类已删除", "success")
    return redirect(url_for("admin.categories"))


# ---------------------------- 订单管理 ----------------------------
@admin_bp.route("/orders")
@admin_required
def orders():
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status")
    keyword = (request.args.get("q") or "").strip()

    query = Order.query
    if status in dict(Order.STATUS_MAP):
        query = query.filter(Order.status == status)
    if keyword:
        query = query.filter(Order.order_no.like(f"%{keyword}%"))

    pagination = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    return render_template(
        "admin/orders.html",
        pagination=pagination,
        orders=pagination.items,
        current_status=status,
        keyword=keyword,
        status_map=Order.STATUS_MAP,
    )


@admin_bp.route("/order/<int:order_id>/ship", methods=["POST"])
@admin_required
def order_ship(order_id):
    order = db.session.get(Order, order_id)
    if order and order.status == Order.STATUS_PENDING:
        order.status = Order.STATUS_SHIPPED
        db.session.commit()
        flash("已发货", "success")
    else:
        flash("当前订单状态不可发货", "warning")
    return redirect(request.form.get("next") or url_for("admin.orders"))


@admin_bp.route("/order/<int:order_id>/delete", methods=["POST"])
@admin_required
def order_delete(order_id):
    order = db.session.get(Order, order_id)
    if order:
        db.session.delete(order)
        db.session.commit()
        flash("订单已删除", "success")
    return redirect(url_for("admin.orders"))


# ---------------------------- 用户管理 ----------------------------
@admin_bp.route("/users")
@admin_required
def users():
    page = request.args.get("page", 1, type=int)
    keyword = (request.args.get("q") or "").strip()
    query = User.query
    if keyword:
        query = query.filter(
            db.or_(User.username.like(f"%{keyword}%"), User.email.like(f"%{keyword}%"))
        )
    pagination = query.order_by(User.id.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    return render_template(
        "admin/users.html",
        pagination=pagination,
        users=pagination.items,
        keyword=keyword,
    )


@admin_bp.route("/user/<int:user_id>/toggle", methods=["POST"])
@admin_required
def user_toggle(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if user.id == current_user.id:
        flash("不能禁用当前登录的账号", "warning")
    else:
        user.is_active_user = not user.is_active_user
        db.session.commit()
        flash("已启用" if user.is_active_user else "已禁用", "success")
    return redirect(url_for("admin.users"))
