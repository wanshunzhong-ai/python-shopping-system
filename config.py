"""
应用配置
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """基础配置"""

    # 密钥：生产环境请通过环境变量覆盖
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me-in-production")

    # 数据库：默认使用 SQLite，文件放在 instance 目录下
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "shopping.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 文件上传
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 单文件最大 5MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}

    # 分页
    PRODUCTS_PER_PAGE = 12
    ORDERS_PER_PAGE = 10

    # 站点信息
    SITE_NAME = "优选商城"
    SITE_SLOGAN = "好物优选 · 品质生活"

    # 货币符号
    CURRENCY = "¥"
