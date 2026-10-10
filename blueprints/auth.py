"""用户认证：注册、登录、退出、个人中心"""
import re

from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_

from extensions import db
from models import Order, User

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _safe_next(default):
    """防止开放重定向"""
    target = request.args.get("next") or request.form.get("next")
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return default


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("shop.index"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""

        errors = []
        if not (3 <= len(username) <= 20):
            errors.append("用户名长度需在 3-20 个字符之间")
        if not re.match(r"^[A-Za-z0-9_\u4e00-\u9fa5]+$", username):
            errors.append("用户名只能包含中英文、数字和下划线")
        if not EMAIL_RE.match(email):
            errors.append("邮箱格式不正确")
        if len(password) < 6:
            errors.append("密码至少 6 位")
        if password != confirm:
            errors.append("两次输入的密码不一致")

        if not errors:
            exists = User.query.filter(
                or_(User.username == username, User.email == email)
            ).first()
            if exists:
                errors.append("用户名或邮箱已被注册")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template(
                "register.html", username=username, email=email
            )

        user = User(username=username, email=email, nickname=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("注册成功，请登录", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("shop.index"))

    if request.method == "POST":
        account = (request.form.get("account") or "").strip()
        password = request.form.get("password") or ""

        user = User.query.filter(
            or_(User.username == account, User.email == account.lower())
        ).first()

        if user and user.check_password(password):
            if not user.is_active_user:
                flash("该账号已被禁用，请联系管理员", "danger")
                return render_template("login.html", account=account)
            login_user(user, remember=bool(request.form.get("remember")))
            flash(f"欢迎回来，{user.nickname or user.username}！", "success")
            return redirect(_safe_next(url_for("shop.index")))

        flash("账号或密码错误", "danger")
        return render_template("login.html", account=account)

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("已安全退出", "info")
    return redirect(url_for("shop.index"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        nickname = (request.form.get("nickname") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        address = (request.form.get("address") or "").strip()

        if phone and not re.match(r"^1[3-9]\d{9}$", phone):
            flash("手机号格式不正确", "danger")
        else:
            current_user.nickname = nickname
            current_user.phone = phone
            current_user.address = address
            db.session.commit()
            flash("资料已更新", "success")
            return redirect(url_for("auth.profile"))

    # 简单的消费统计
    orders = current_user.orders.order_by(Order.created_at.desc()).all()
    total_spent = sum(
        o.total_amount for o in orders if o.status != Order.STATUS_CANCELED
    )
    stats = {
        "order_count": len(orders),
        "total_spent": total_spent,
        "recent": orders[:5],
    }
    return render_template("profile.html", stats=stats)


@auth_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    old = request.form.get("old_password") or ""
    new = request.form.get("new_password") or ""
    confirm = request.form.get("confirm_password") or ""

    if not current_user.check_password(old):
        flash("原密码不正确", "danger")
    elif len(new) < 6:
        flash("新密码至少 6 位", "danger")
    elif new != confirm:
        flash("两次输入的新密码不一致", "danger")
    else:
        current_user.set_password(new)
        db.session.commit()
        flash("密码修改成功", "success")

    return redirect(url_for("auth.profile"))
