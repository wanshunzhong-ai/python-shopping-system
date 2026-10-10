"""商城前台：首页、商品列表、商品详情"""
from flask import Blueprint, current_app, render_template, request, abort
from sqlalchemy import or_

from extensions import db
from models import Category, Product

shop_bp = Blueprint("shop", __name__)


def _query_products():
    """根据请求参数构建商品查询（搜索 / 分类 / 排序）"""
    keyword = (request.args.get("q") or "").strip()
    category_id = request.args.get("category", type=int)
    sort = request.args.get("sort", "default")

    query = Product.query.filter_by(is_active=True)

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(Product.name.like(like),
                Product.summary.like(like),
                Product.description.like(like))
        )

    if category_id:
        query = query.filter(Product.category_id == category_id)

    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort == "sales":
        query = query.order_by(Product.sales.desc())
    elif sort == "new":
        query = query.order_by(Product.created_at.desc())
    else:
        query = query.order_by(Product.id.asc())

    return query, keyword, category_id, sort


@shop_bp.route("/")
def index():
    per_page = current_app.config["PRODUCTS_PER_PAGE"]
    query, keyword, category_id, sort = _query_products()
    page = request.args.get("page", 1, type=int)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    categories = Category.query.order_by(Category.sort_order, Category.id).all()
    hot_products = (
        Product.query.filter_by(is_active=True)
        .order_by(Product.sales.desc())
        .limit(8)
        .all()
    )
    new_products = (
        Product.query.filter_by(is_active=True)
        .order_by(Product.created_at.desc(), Product.id.desc())
        .limit(8)
        .all()
    )

    return render_template(
        "index.html",
        pagination=pagination,
        products=pagination.items,
        categories=categories,
        hot_products=hot_products,
        new_products=new_products,
        keyword=keyword,
        current_category=category_id,
        sort=sort,
        is_home=True,
    )


@shop_bp.route("/products")
def product_list():
    per_page = current_app.config["PRODUCTS_PER_PAGE"]
    query, keyword, category_id, sort = _query_products()
    page = request.args.get("page", 1, type=int)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    categories = Category.query.order_by(Category.sort_order, Category.id).all()
    current_cat = db.session.get(Category, category_id) if category_id else None

    return render_template(
        "products.html",
        pagination=pagination,
        products=pagination.items,
        categories=categories,
        keyword=keyword,
        current_category=category_id,
        current_cat=current_cat,
        sort=sort,
    )


@shop_bp.route("/product/<int:product_id>")
def product_detail(product_id):
    product = db.session.get(Product, product_id)
    if not product or not product.is_active:
        abort(404)

    # 同分类相关推荐
    related = (
        Product.query.filter(
            Product.is_active == True,  # noqa: E712
            Product.category_id == product.category_id,
            Product.id != product.id,
        )
        .order_by(Product.sales.desc())
        .limit(4)
        .all()
    )

    return render_template("product_detail.html", product=product, related=related)
