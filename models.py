"""
数据模型定义
"""
import datetime
import random
import string

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db, login_manager


def now():
    return datetime.datetime.now()


class User(UserMixin, db.Model):
    """用户"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active_user = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=now)

    cart_items = db.relationship(
        "CartItem", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    orders = db.relationship(
        "Order", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    @property
    def is_active(self):
        """Flask-Login 使用：被禁用的用户无法登录"""
        return self.is_active_user

    @property
    def cart_count(self):
        return sum(item.quantity for item in self.cart_items)

    def __repr__(self):
        return f"<User {self.username}>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Category(db.Model):
    """商品分类"""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    icon = db.Column(db.String(20), default="📦")  # emoji 图标
    description = db.Column(db.String(255))
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=now)

    products = db.relationship("Product", backref="category", lazy="dynamic")

    def __repr__(self):
        return f"<Category {self.name}>"


class Product(db.Model):
    """商品"""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    price = db.Column(db.Numeric(10, 2, asdecimal=False), nullable=False)
    original_price = db.Column(db.Numeric(10, 2, asdecimal=False))
    stock = db.Column(db.Integer, default=0, nullable=False)
    sales = db.Column(db.Integer, default=0, nullable=False)
    image = db.Column(db.String(255))  # 相对 static 的路径，或完整 http 链接
    summary = db.Column(db.String(255))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

    cart_items = db.relationship(
        "CartItem", backref="product", lazy="dynamic", cascade="all, delete-orphan"
    )

    @property
    def discount(self):
        """折扣，如 8.5 折"""
        if self.original_price and self.original_price > self.price:
            return round(self.price / self.original_price * 10, 1)
        return None

    def __repr__(self):
        return f"<Product {self.name}>"


class CartItem(db.Model):
    """购物车条目"""

    __tablename__ = "cart_items"
    __table_args__ = (db.UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    created_at = db.Column(db.DateTime, default=now)

    @property
    def subtotal(self):
        return round((self.product.price or 0) * self.quantity, 2)


class Order(db.Model):
    """订单"""

    __tablename__ = "orders"

    STATUS_PENDING = "pending"      # 待发货
    STATUS_SHIPPED = "shipped"      # 已发货 / 待收货
    STATUS_DONE = "done"            # 已完成
    STATUS_CANCELED = "canceled"    # 已取消

    STATUS_MAP = {
        STATUS_PENDING: ("待发货", "warning"),
        STATUS_SHIPPED: ("待收货", "info"),
        STATUS_DONE: ("已完成", "success"),
        STATUS_CANCELED: ("已取消", "secondary"),
    }

    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(32), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2, asdecimal=False), nullable=False)
    status = db.Column(db.String(20), default=STATUS_PENDING, nullable=False)
    receiver_name = db.Column(db.String(50), nullable=False)
    receiver_phone = db.Column(db.String(20), nullable=False)
    receiver_address = db.Column(db.String(255), nullable=False)
    payment_method = db.Column(db.String(20), default="在线支付")
    remark = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

    items = db.relationship(
        "OrderItem", backref="order", lazy="joined", cascade="all, delete-orphan"
    )

    @property
    def status_text(self):
        return self.STATUS_MAP.get(self.status, ("未知", "secondary"))[0]

    @property
    def status_color(self):
        return self.STATUS_MAP.get(self.status, ("未知", "secondary"))[1]

    @property
    def total_quantity(self):
        return sum(i.quantity for i in self.items)

    @staticmethod
    def generate_order_no():
        ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        rand = "".join(random.choices(string.digits, k=4))
        return f"{ts}{rand}"

    def __repr__(self):
        return f"<Order {self.order_no}>"


class OrderItem(db.Model):
    """订单明细（下单时快照商品信息）"""

    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    product_name = db.Column(db.String(120), nullable=False)
    product_image = db.Column(db.String(255))
    price = db.Column(db.Numeric(10, 2, asdecimal=False), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    @property
    def subtotal(self):
        return round((self.price or 0) * self.quantity, 2)
