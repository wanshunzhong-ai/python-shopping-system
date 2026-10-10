"""
优选商城 —— Python 购物网站
应用入口：创建 Flask 应用、注册蓝图、注册模板过滤器
"""
import os

from flask import Flask, render_template, request, url_for

from config import Config
from extensions import db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # 确保目录存在
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)

    # 导入模型，保证建表时被注册
    from models import Category, Order, OrderItem, Product, User  # noqa: F401

    # ---------------- 模板过滤器 / 全局变量 ----------------
    @app.template_filter("money")
    def money_filter(value):
        """金额格式化：1288.0 -> 1,288.00"""
        try:
            return f"{float(value):,.2f}"
        except (TypeError, ValueError):
            return "0.00"

    @app.template_filter("img")
    def img_filter(path):
        """图片地址：支持外链与本地相对路径"""
        if not path:
            return url_for("static", filename="img/placeholder.svg")
        if path.startswith(("http://", "https://", "data:")):
            return path
        return url_for("static", filename=path)

    @app.context_processor
    def inject_globals():
        from flask_login import current_user

        from models import Category

        cart_count = 0
        if current_user.is_authenticated:
            cart_count = current_user.cart_count

        nav_categories = Category.query.order_by(
            Category.sort_order, Category.id
        ).all()

        return {
            "site_name": app.config["SITE_NAME"],
            "site_slogan": app.config["SITE_SLOGAN"],
            "currency": app.config["CURRENCY"],
            "cart_count": cart_count,
            "nav_categories": nav_categories,
        }

    # ---------------- 注册蓝图 ----------------
    from blueprints.admin import admin_bp
    from blueprints.auth import auth_bp
    from blueprints.cart import cart_bp
    from blueprints.order import order_bp
    from blueprints.shop import shop_bp

    app.register_blueprint(shop_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(cart_bp, url_prefix="/cart")
    app.register_blueprint(order_bp, url_prefix="/order")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # ---------------- 错误页面 ----------------
    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="页面走丢了～"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403, message="没有权限访问该页面"), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template("error.html", code=500, message="服务器开小差了"), 500

    # ---------------- 命令行工具 ----------------
    @app.cli.command("init-db")
    def init_db_command():
        """初始化数据库表"""
        db.create_all()
        print("数据库表已创建")

    @app.cli.command("seed")
    def seed_command():
        """填充演示数据"""
        from seed import run_seed

        run_seed(app)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
