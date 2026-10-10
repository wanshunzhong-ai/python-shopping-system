"""冒烟测试：跑通主要流程"""
import re
from app import app
from extensions import db
from models import Product, Order, User

app.config["WTF_CSRF_ENABLED"] = False
c = app.test_client()
fails = []


def check(name, cond, extra=""):
    print(("  [OK] " if cond else "  [FAIL] ") + name + ("  " + str(extra) if extra else ""))
    if not cond:
        fails.append(name)


print("== 前台 ==")
r = c.get("/")
check("首页 200", r.status_code == 200, r.status_code)
check("首页含商品", "加入购物车" in r.get_data(as_text=True))
check("首页含分类", "手机数码" in r.get_data(as_text=True))

r = c.get("/products?sort=price_asc&q=耳机")
check("搜索+排序 200", r.status_code == 200)

r = c.get("/products?category=1")
check("分类筛选 200", r.status_code == 200)

r = c.get("/product/1")
check("商品详情 200", r.status_code == 200)

r = c.get("/product/99999")
check("不存在商品 404", r.status_code == 404)

print("== 注册登录 ==")
r = c.post("/auth/register", data={
    "username": "testuser", "email": "test@t.com",
    "password": "123456", "confirm": "123456"}, follow_redirects=True)
check("注册成功", "注册成功" in r.get_data(as_text=True))

r = c.post("/auth/login", data={"account": "testuser", "password": "123456"},
           follow_redirects=True)
check("登录成功", "欢迎回来" in r.get_data(as_text=True))

r = c.get("/auth/logout", follow_redirects=True)
r = c.post("/auth/login", data={"account": "testuser", "password": "wrong"},
           follow_redirects=True)
check("错误密码拦截", "账号或密码错误" in r.get_data(as_text=True))

# 重新登录
c.post("/auth/login", data={"account": "testuser", "password": "123456"})

print("== 购物车 ==")
r = c.post("/cart/add/1", data={"quantity": 2})
check("加入购物车", r.status_code in (302, 200), r.status_code)
r = c.post("/cart/add/2", data={"quantity": 1})
r = c.get("/cart/")
html = r.get_data(as_text=True)
check("购物车 200", r.status_code == 200)
check("购物车有商品", "订单摘要" in html)

# AJAX 加购
r = c.post("/cart/add/3", data={"quantity": 1},
           headers={"X-Requested-With": "XMLHttpRequest"})
check("AJAX 加购返回 JSON", r.is_json and r.get_json().get("ok"), r.get_json())

print("== 下单 ==")
r = c.get("/order/checkout")
check("结算页 200", r.status_code == 200)
r = c.post("/order/checkout", data={
    "receiver_name": "张三", "receiver_phone": "13800138000",
    "receiver_address": "北京市朝阳区xx路1号",
    "payment_method": "在线支付", "remark": "尽快发货"}, follow_redirects=True)
html = r.get_data(as_text=True)
check("下单成功", "下单成功" in html, r.status_code)
m = re.search(r"/order/(\d+)", r.request.path if hasattr(r, "request") else "")
order_id = int(r.request.path.rstrip("/").split("/")[-1]) if r.request.path.startswith("/order/") else None
check("跳转订单详情", order_id is not None, r.request.path)

r = c.get("/order/list")
check("订单列表 200", r.status_code == 200)
check("订单列表有单", "张三" in r.get_data(as_text=True) or "订单号" in r.get_data(as_text=True))

if order_id:
    r = c.get(f"/order/{order_id}")
    check("订单详情 200", r.status_code == 200)
    r = c.post(f"/order/{order_id}/cancel", follow_redirects=True)
    check("取消订单", "订单已取消" in r.get_data(as_text=True))

print("== 权限控制 ==")
c.get("/auth/logout")
r = c.get("/cart/")
check("未登录访问购物车跳登录", r.status_code == 302 and "/auth/login" in r.headers.get("Location", ""))
r = c.get("/admin/")
check("未登录访问后台跳登录", r.status_code == 302)

print("== 后台管理 ==")
r = c.post("/auth/login", data={"account": "admin", "password": "admin123"},
           follow_redirects=True)
check("管理员登录", "欢迎回来" in r.get_data(as_text=True))

for path, name in [("/admin/", "仪表盘"), ("/admin/products", "商品管理"),
                   ("/admin/categories", "分类管理"), ("/admin/orders", "订单管理"),
                   ("/admin/users", "用户管理"), ("/admin/product/new", "新增商品页")]:
    r = c.get(path)
    check(f"{name} 200", r.status_code == 200, r.status_code)

# 新增分类 -> 新增商品 -> 编辑 -> 上下架 -> 删除
r = c.post("/admin/categories", data={"name": "测试分类", "icon": "🧪", "sort_order": 99},
           follow_redirects=True)
check("新增分类", "分类已添加" in r.get_data(as_text=True))

with app.app_context():
    from models import Category
    cat = Category.query.filter_by(name="测试分类").first()
    cat_id = cat.id if cat else None

r = c.post("/admin/product/new", data={
    "name": "测试商品AA", "category_id": cat_id, "price": "19.9",
    "original_price": "29.9", "stock": "5", "summary": "测试用",
    "description": "描述内容", "is_active": "on"}, follow_redirects=True)
check("新增商品", "商品创建成功" in r.get_data(as_text=True))

with app.app_context():
    p = Product.query.filter_by(name="测试商品AA").first()
    pid = p.id if p else None
check("商品写入数据库", pid is not None)

r = c.post(f"/admin/product/{pid}/edit", data={
    "name": "测试商品BB", "category_id": cat_id, "price": "29.9",
    "stock": "8", "summary": "改过了", "is_active": "on"}, follow_redirects=True)
check("编辑商品", "商品已更新" in r.get_data(as_text=True))

r = c.post(f"/admin/product/{pid}/toggle", follow_redirects=True)
check("商品下架", "已下架" in r.get_data(as_text=True))

r = c.post(f"/admin/product/{pid}/delete", follow_redirects=True)
check("删除商品", "商品已删除" in r.get_data(as_text=True))

r = c.post(f"/admin/category/{cat_id}/delete", follow_redirects=True)
check("删除分类", "分类已删除" in r.get_data(as_text=True))

# 发货流程
with app.app_context():
    demo = User.query.filter_by(username="demo").first()
    o = Order(user_id=demo.id, order_no=Order.generate_order_no(), total_amount=99.0,
              receiver_name="李四", receiver_phone="13900139000",
              receiver_address="上海市浦东新区yy路2号", status=Order.STATUS_PENDING)
    db.session.add(o)
    db.session.commit()
    pending_id = o.id

r = c.post(f"/admin/order/{pending_id}/ship", follow_redirects=True)
check("订单发货", "已发货" in r.get_data(as_text=True))

c.get("/auth/logout")
c.post("/auth/login", data={"account": "demo", "password": "123456"})
r = c.post(f"/order/{pending_id}/confirm", follow_redirects=True)
check("确认收货", "已确认收货" in r.get_data(as_text=True))

print()
print("=" * 42)
print("  失败项：", len(fails), fails if fails else "无")
print("=" * 42)
