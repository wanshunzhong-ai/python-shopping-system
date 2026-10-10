# 优选商城 · Python 购物网站

基于 **Flask + SQLite** 开发的全功能购物网站，包含商城前台与后台管理系统。

---

## 一、技术栈

| 层次 | 技术 |
|------|------|
| 后端框架 | Python 3.8+ / Flask 3.x |
| ORM | Flask-SQLAlchemy（SQLAlchemy 2.x） |
| 认证 | Flask-Login（Session 会话 + 密码哈希） |
| 数据库 | SQLite（零配置，文件型，可平滑切换 MySQL） |
| 前端 | Jinja2 模板 + Bootstrap 5 + Bootstrap Icons |
| 架构 | 应用工厂 + 蓝图（Blueprint）模块化 |

> 所有前端资源（Bootstrap、图标字体）已本地化到 `static/vendor/`，**断网也能正常显示**。

---

## 二、功能清单

### 商城前台
- **首页**：轮播式 Hero 区、分类导航、热销榜单、新品上架、全部商品
- **商品浏览**：分类筛选、关键词搜索（名称/简介/详情）、5 种排序（综合/销量/最新/价格升降）、分页
- **商品详情**：大图、折扣标签、库存与销量、数量步进器、加入购物车 / 立即购买、相关推荐
- **用户系统**：注册（含格式校验）、登录（用户名或邮箱）、退出、记住我
- **购物车**：加购（AJAX 无刷新 + 角标动画）、改数量、删除、清空、实时小计与总额
- **下单结算**：收货信息、支付方式、订单备注、库存校验、下单自动扣减库存
- **我的订单**：按状态筛选、订单卡片、订单详情、状态进度条
- **订单流转**：取消订单（自动回滚库存）、确认收货
- **个人中心**：资料修改、修改密码、消费统计、最近订单

### 后台管理（`/admin`）
- **数据概览**：销售额/订单/商品/用户四大指标、订单状态分布、热销 Top5、**库存预警**
- **商品管理**：列表查询、新增、编辑、上下架、删除、**图片上传**（本地文件或外链）
- **分类管理**：新增、编辑（弹窗）、删除（有商品的分类受保护）
- **订单管理**：按状态/订单号查询、**一键发货**、查看详情、删除
- **用户管理**：查询、启用/禁用账号、角色标识

### 安全与健壮性
- 密码 `werkzeug` 哈希存储，明文不落库
- 所有 SQL 走 ORM 参数化，天然防注入
- 所有写操作使用 POST 方法
- 后台路由统一 `@admin_required` 鉴权，越权返回 403
- 订单/购物车校验资源归属，防止水平越权
- 登录跳转 `next` 参数校验，防开放重定向
- 上传文件白名单校验（扩展名） + UUID 重命名，防路径穿越
- 自定义 403 / 404 / 500 错误页

---

## 三、快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 初始化数据库与演示数据

```bash
python seed.py
```

### 3. 启动

```bash
python app.py
```

浏览器打开 <http://127.0.0.1:5000>

> Windows 用户可直接双击 **`start.bat`**，脚本会自动完成以上三步（含创建虚拟环境）。

### 演示账号

| 角色 | 账号 | 密码 | 入口 |
|------|------|------|------|
| 管理员 | `admin` | `admin123` | 登录后右上角「后台管理」或访问 `/admin` |
| 普通用户 | `demo` | `123456` | 商城前台 |

---

## 四、项目结构

```
Shopping/
├── app.py                  # 应用入口：工厂函数、蓝图注册、模板过滤器、错误页
├── config.py               # 配置（数据库、上传、分页、站点信息）
├── extensions.py           # 扩展实例（db / login_manager）
├── models.py               # 数据模型：User / Category / Product / CartItem / Order / OrderItem
├── seed.py                 # 初始化演示数据 + 生成商品 SVG 占位图
├── smoke_test.py           # 冒烟测试（41 项断言，覆盖全流程）
├── requirements.txt
├── start.bat               #   Windows 一键启动脚本
├── blueprints/             # 业务蓝图
│   ├── shop.py             #   商品浏览 / 搜索 / 详情
│   ├── auth.py             #   注册 / 登录 / 个人中心
│   ├── cart.py             #   购物车
│   ├── order.py            #   结算 / 订单
│   └── admin.py            #   后台管理
├── templates/              # Jinja2 模板
│   ├── base.html           #   前台母版
│   ├── _product_card.html  #   商品卡片（复用组件）
│   ├── index.html / products.html / product_detail.html
│   ├── cart.html / checkout.html / orders.html / order_detail.html
│   ├── login.html / register.html / profile.html / error.html
│   └── admin/              #   后台母版与各管理页
├── static/
│   ├── css/style.css       #   前台样式
│   ├── css/admin.css       #   后台样式
│   ├── js/main.js          #   步进器 / AJAX 加购 / 提示 / 图片预览
│   ├── vendor/             #   本地化 Bootstrap 5 + Icons
│   ├── img/placeholder.svg
│   └── uploads/            #   商品图片（seed 生成的占位图 + 后台上传）
└── instance/shopping.db    #   SQLite 数据库（运行 seed 后生成）
```

---

## 五、数据模型（ER 概览）

```
User 1───n CartItem n───1 Product n───1 Category
User 1───n Order    1───n OrderItem
```

| 表 | 说明 | 关键字段 |
|----|------|---------|
| `users` | 用户 | username、email、password_hash、is_admin、is_active_user |
| `categories` | 分类 | name、icon、sort_order |
| `products` | 商品 | name、price、original_price、stock、sales、image、is_active |
| `cart_items` | 购物车 | user_id + product_id 唯一约束、quantity |
| `orders` | 订单 | order_no、total_amount、status、收货信息 |
| `order_items` | 订单明细 | 商品信息快照（名称/图片/单价），保证历史订单不受商品变更影响 |

订单状态机：

```
pending(待发货) ──发货──> shipped(待收货) ──确认收货──> done(已完成)
     │
     └──取消──> canceled(已取消，库存自动回滚)
```

---

## 六、常见操作

### 重置演示数据

```bash
python seed.py --reset
```

### 切换到 MySQL

1. 安装驱动：`pip install PyMySQL`
2. 修改 `config.py` 中的连接串：

```python
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://用户名:密码@127.0.0.1:3306/shopping?charset=utf8mb4"
```

3. 执行 `python seed.py --reset` 重新建表填数据。
   （模型定义不依赖任何 SQLite 专有特性，可直接迁移。）

### 运行冒烟测试

```bash
python smoke_test.py
```

---

## 七、注意事项

- 生产部署请通过环境变量设置 `SECRET_KEY`，并关闭 `debug=True`。
- 数据库文件位于 `instance/shopping.db`，删除该文件后重新执行 `python seed.py` 即可完全重置。
- 上传的图片存放在 `static/uploads/`，请勿在部署时遗漏该目录。
