"""
演示数据：初始化分类、商品、管理员与普通用户，并生成商品占位图（SVG，离线可用）
用法：
    python seed.py            # 建表 + 填充数据（已存在则跳过）
    python seed.py --reset    # 清空并重建
"""
import os
import sys

from config import Config
from extensions import db
from models import Category, Order, OrderItem, Product, User

# ---------------------------- 商品数据 ----------------------------
CATALOG = [
    ("手机数码", "📱", "智能手机、平板、耳机等", [
        ("星辰 Pro 5G 智能手机 12GB+256GB", 3999, 4599, 120, 860,
         "6.7 英寸 OLED 直屏，旗舰影像系统",
         "搭载新一代旗舰芯片，6.7 英寸 120Hz OLED 屏幕，5000mAh 大电池支持 120W 快充。后置 5000 万像素三摄，支持光学防抖与 8K 视频录制。12GB+256GB 存储组合，畅玩大型游戏无压力。"),
        ("极光无线降噪耳机 Air 3", 699, 899, 340, 1520,
         "主动降噪 40dB，超长续航 36 小时",
         "双馈主动降噪深度可达 40dB，通勤路上瞬间安静。支持蓝牙 5.3 与低延迟游戏模式，单次续航 9 小时，配合充电仓总续航 36 小时。IPX5 防水，运动流汗也不怕。"),
        ("幻影 13 英寸平板电脑 8GB+128GB", 2599, 2999, 88, 430,
         "2.8K 高刷屏，支持手写笔与键盘",
         "13 英寸 2.8K 144Hz 高刷新率屏幕，十核处理器，8GB+128GB 存储。支持选配磁吸手写笔与妙控键盘，轻松切换影音娱乐与轻办公场景。"),
        ("快充宝 20000mAh 移动电源", 159, 199, 600, 3210,
         "22.5W 双向快充，可上飞机",
         "20000mAh 大容量，支持 22.5W 双向快充，可为手机充电约 4 次。双 USB-A + Type-C 三口输出，出差旅行必备。"),
        ("智能手环 8 NFC 版", 249, 299, 420, 1980,
         "血氧心率监测，14 天续航",
         "1.62 英寸 AMOLED 高清彩屏，支持全天候心率、血氧与睡眠监测。内置 NFC，可刷公交门禁。典型续航 14 天，5ATM 防水。"),
    ]),
    ("电脑办公", "💻", "笔记本、显示器、外设", [
        ("凌云 14 英寸轻薄笔记本 i7/16G/512G", 5299, 5999, 60, 320,
         "1.2kg 轻薄机身，2.8K 护眼屏",
         "第 13 代酷睿 i7 处理器，16GB LPDDR5 内存 + 512GB SSD。14 英寸 2.8K 90Hz 护眼屏，整机重量仅 1.2kg，长续航满足全天移动办公。"),
        ("27 英寸 2K 高清显示器 165Hz", 1099, 1399, 150, 640,
         "IPS 面板，广色域低蓝光",
         "27 英寸 2K 分辨率 IPS 面板，165Hz 刷新率 1ms 响应，覆盖 95% DCI-P3 广色域。支持升降旋转支架，附带低蓝光不闪屏认证。"),
        ("机械键盘 87 键 客制化热插拔", 359, 459, 280, 1120,
         "Gasket 结构，三模连接",
         "87 键紧凑布局，Gasket 结构配硅胶垫，手感软弹。支持有线 / 蓝牙 / 2.4G 三模连接，热插拔轴座可自由换轴，RGB 全键无冲。"),
        ("人体工学无线鼠标 静音版", 129, 169, 500, 2210,
         "静音微动，6 档 DPI 可调",
         "贴合手型的人体工学设计，静音微动适合办公环境。6 档 DPI 一键切换，2.4G 无线连接稳定，一节电池可用约 12 个月。"),
        ("便携激光打印机 家用办公", 899, 1099, 70, 210,
         "无线打印，手机直连",
         "支持手机 APP 无线直连打印，打印速度 22 页/分钟。鼓粉分离设计，耗材成本更低，适合家庭与小型办公。"),
    ]),
    ("家用电器", "🏠", "厨房、清洁、生活电器", [
        ("智能扫地机器人 自清洁版", 2299, 2899, 90, 410,
         "激光导航，自动集尘",
         "LDS 激光导航精准建图，支持 APP 分区清扫与虚拟墙。基站自动集尘 + 自动洗拖布，4000Pa 强劲吸力，地毯识别自动增压。"),
        ("静音空气循环扇 落地式", 399, 499, 260, 780,
         "直流变频，9 档风力",
         "直流变频电机，最低运行噪音仅 28dB。9 档风力调节，支持上下左右自动摆头，可搭配空调快速均衡室温。"),
        ("多功能电烤箱 32L 家用", 599, 799, 180, 520,
         "上下独立控温，内置照明",
         "32L 大容量可容纳 10 寸披萨，上下管独立控温，精准控温 ±5℃。内置照明灯与发酵功能，附赠烤盘、烤网、旋转烤叉。"),
        ("破壁料理机 加热免滤", 459, 599, 220, 930,
         "一键热饮，8 叶钝刀",
         "8 叶钝刀高速破壁，可打豆浆、米糊、浓汤、果汁。自带加热功能，一键热饮免过滤，12 小时预约定时。"),
        ("全自动咖啡机 意式家用", 1699, 2199, 80, 260,
         "一键拿铁，20Bar 萃取",
         "20Bar 高压萃取意式浓缩，内置研磨器现磨现萃。一键制作拿铁、卡布奇诺，奶泡绵密顺滑，家用咖啡馆体验。"),
    ]),
    ("服饰鞋包", "👕", "男装、女装、鞋靴、箱包", [
        ("纯棉基础款圆领 T 恤（男）", 99, 149, 800, 3420,
         "260g 重磅纯棉，多色可选",
         "260g 重磅新疆长绒棉，柔软亲肤不易变形。经典圆领版型，落肩设计更显休闲，多色可选百搭日常。"),
        ("轻薄羽绒服 90 白鸭绒（女）", 499, 799, 300, 890,
         "90% 白鸭绒，可收纳便携",
         "填充 90% 白鸭绒，蓬松度 600+，保暖轻盈。面料防泼水，附赠收纳袋可压缩成巴掌大小，出行携带方便。"),
        ("缓震运动跑鞋 男款", 399, 559, 450, 1650,
         "回弹中底，透气网面",
         "高回弹中底科技，有效缓解落地冲击。一体织透气网面，长时间运动保持干爽，橡胶大底防滑耐磨。"),
        ("真皮通勤单肩包（女）", 359, 519, 200, 620,
         "头层牛皮，多隔层收纳",
         "头层牛皮材质，纹理细腻耐用。内部多隔层设计，可放 13 寸笔记本、平板与日常用品，通勤出街两相宜。"),
        ("轻量行李箱 24 寸 万向轮", 429, 599, 260, 740,
         "PC 材质，静音万向轮",
         "德国拜耳 PC 材质箱体，抗压回弹。360° 静音万向轮 + TSA 海关锁，24 寸登机托运两用，内部干湿分离。"),
    ]),
    ("食品生鲜", "🍎", "零食、粮油、水果", [
        ("每日坚果混合装 750g（30 包）", 89, 129, 900, 4120,
         "7 种坚果果干，独立小包",
         "精选巴旦木、腰果、核桃仁、蔓越莓等 7 种坚果果干。每包 25g 独立包装，新鲜锁鲜，办公加餐随时补充能量。"),
        ("五常大米 10kg 真空装", 99, 139, 700, 2360,
         "东北稻花香，当季新米",
         "源自黑龙江五常核心产区稻花香 2 号，当季新米真空锁鲜。米粒饱满油亮，蒸煮后饭香浓郁、口感软糯。"),
        ("冷萃精品挂耳咖啡 20 包", 79, 109, 850, 2980,
         "中深烘焙，现磨锁鲜",
         "精选云南与埃塞俄比亚拼配豆，中深烘焙。独立氮气锁鲜包装，撕开冲泡 3 分钟即可享用一杯手冲级咖啡。"),
        ("有机初榨橄榄油 750ml", 128, 168, 400, 860,
         "冷压初榨，酸度≤0.3",
         "西班牙原装进口，冷压初榨工艺，酸度低于 0.3%。适合凉拌、低温烹饪，果香清新不腻口。"),
        ("新疆冰糖心苹果 5 斤装", 59, 89, 620, 1730,
         "阿克苏产区，脆甜多汁",
         "新疆阿克苏产区日照充足，昼夜温差大形成独特冰糖心。果肉脆甜多汁，单果 200-300g，产地直发新鲜到家。"),
    ]),
    ("图书文娱", "📚", "图书、文具、乐器", [
        ("《Python 编程从入门到实践》", 79, 108, 500, 1890,
         "全彩印刷，附源码下载",
         "畅销 Python 入门经典，全彩印刷讲解清晰。涵盖基础语法、Web 开发、数据可视化与实战项目，附赠全部源码与习题答案。"),
        ("《deep learning 深度学习》精装版", 128, 168, 300, 720,
         "深度学习经典教材",
         "深度学习领域奠基性著作中文版，系统讲解神经网络、卷积网络、循环网络与生成模型。适合研究生与工程实践者。"),
        ("中性笔 0.5mm 黑色 20 支装", 25, 39, 1200, 4560,
         "速干顺滑，考试专用",
         "0.5mm 子弹头笔尖，书写顺滑出墨均匀。速干油墨不易蹭花，握感舒适，考试办公两相宜。"),
        ("尤克里里 23 寸初学者套装", 259, 359, 180, 430,
         "桃花芯木，附全套配件",
         "23 寸桃花芯木尤克里里，音色温暖明亮。附赠调音器、拨片、背带、琴包与入门教程，零基础轻松上手。"),
        ("手账本 A5 创意胶套本", 39, 59, 700, 1560,
         "100g 顺滑纸张，不洇墨",
         "A5 尺寸创意封面，内含 100g 顺滑纸张共 200 页，钢笔书写不洇墨不透页。附赠贴纸与书签，记录生活好帮手。"),
    ]),
    ("家居家装", "🛋️", "家具、床品、收纳", [
        ("乳胶记忆棉护颈枕 一对装", 159, 229, 520, 1340,
         "泰国乳胶，慢回弹支撑",
         "泰国进口天然乳胶含量 90% 以上，慢回弹贴合颈椎曲线。透气孔设计散热排湿，附赠可拆洗针织枕套。"),
        ("全棉四件套 1.8m 床", 299, 429, 380, 970,
         "60 支长绒棉，亲肤透气",
         "60 支新疆长绒棉，密度 200 根/英寸，柔软亲肤。活性印染不易掉色，适用 1.8m 床，含被套、床单、枕套两只。"),
        ("北欧简约落地灯 三档调光", 259, 359, 240, 510,
         "暖光护眼，遥控调光",
         "北欧简约设计，亚麻灯罩柔和不刺眼。支持三档色温与无级调光，附遥控器，适合客厅与卧室阅读照明。"),
        ("折叠收纳箱 66L 加厚款", 59, 89, 900, 2680,
         "棉麻材质，可折叠省空间",
         "66L 大容量加厚棉麻收纳箱，内置钢架支撑不变形。不用时可折叠收纳，适合衣物、被褥与杂物整理。"),
        ("香薰蜡烛礼盒 三支装", 129, 179, 460, 820,
         "天然大豆蜡，淡雅香调",
         "天然大豆蜡搭配植物精油，燃烧无黑烟。含鼠尾草、雪松、白茶三种香型，燃烧时长各约 30 小时，礼盒包装适合送礼。"),
    ]),
    ("运动户外", "⚽", "健身、骑行、露营", [
        ("瑜伽垫 TPE 加厚防滑 8mm", 129, 189, 600, 1920,
         "双面防滑，环保无异味",
         "TPE 环保材质无毒无异味，8mm 加厚回弹缓冲。双面防滑纹理，附赠绑带与背带，居家健身与户外皆适用。"),
        ("可调节哑铃 20kg 一对", 399, 559, 260, 640,
         "快速调节，占空间小",
         "一对可调节哑铃，总重 20kg，通过旋钮快速更换配重片。替代整套哑铃架，居家健身节省空间。"),
        ("山地自行车 27.5 寸 21 速", 1299, 1699, 90, 230,
         "铝合金车架，双碟刹",
         "27.5 寸铝合金车架轻量耐用，21 速禧玛诺变速系统。前后双碟刹制动灵敏，避震前叉应对颠簸路面。"),
        ("户外露营天幕 3x3m 防晒", 269, 399, 300, 580,
         "UPF50+，附撑杆地钉",
         "3x3m 大尺寸天幕，面料 UPF50+ 有效阻隔紫外线。附赠 2 根撑杆、8 根地钉与风绳，露营野餐遮阳挡雨。"),
        ("保温运动水壶 1L 不锈钢", 89, 129, 700, 2140,
         "24 小时保温，316 内胆",
         "316 食品级不锈钢内胆，24 小时保温保冷。1L 大容量，一键弹盖单手开启，附提绳便于携带。"),
    ]),
]

DEMO_USERS = [
    ("admin", "admin@shop.com", "admin123", True, "管理员"),
    ("demo", "demo@shop.com", "123456", False, "演示用户"),
    ("alice", "alice@shop.com", "123456", False, "小艾"),
]

# 占位图配色
PALETTE = [
    ("#6366f1", "#8b5cf6"), ("#ec4899", "#f472b6"), ("#f59e0b", "#fbbf24"),
    ("#10b981", "#34d399"), ("#3b82f6", "#60a5fa"), ("#ef4444", "#f87171"),
    ("#14b8a6", "#2dd4bf"), ("#8b5cf6", "#a78bfa"),
]


def make_svg(name, emoji, index, folder):
    """生成一张带渐变背景与文字的 SVG 占位图"""
    c1, c2 = PALETTE[index % len(PALETTE)]
    short = name if len(name) <= 12 else name[:12] + "…"
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 600 600">
  <defs>
    <linearGradient id="g{index}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{c1}"/>
      <stop offset="100%" stop-color="{c2}"/>
    </linearGradient>
  </defs>
  <rect width="600" height="600" fill="url(#g{index})"/>
  <circle cx="480" cy="120" r="160" fill="#ffffff" opacity="0.10"/>
  <circle cx="120" cy="500" r="120" fill="#ffffff" opacity="0.08"/>
  <text x="300" y="300" font-size="180" text-anchor="middle" dominant-baseline="central">{emoji}</text>
  <text x="300" y="470" font-size="34" fill="#ffffff" text-anchor="middle"
        font-family="'Microsoft YaHei','PingFang SC',sans-serif" font-weight="600">{short}</text>
</svg>'''
    filename = f"seed_{index}.svg"
    with open(os.path.join(folder, filename), "w", encoding="utf-8") as f:
        f.write(svg)
    return f"uploads/{filename}"


PLACEHOLDER_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 600 600">
  <rect width="600" height="600" fill="#eef1f6"/>
  <text x="300" y="290" font-size="150" text-anchor="middle" dominant-baseline="central">🛍️</text>
  <text x="300" y="420" font-size="30" fill="#9aa4b2" text-anchor="middle"
        font-family="'Microsoft YaHei','PingFang SC',sans-serif">暂无图片</text>
</svg>'''


def run_seed(app, reset=False):
    upload_dir = app.config["UPLOAD_FOLDER"]
    img_dir = os.path.join(app.static_folder, "img")
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(img_dir, exist_ok=True)

    # 通用占位图
    with open(os.path.join(img_dir, "placeholder.svg"), "w", encoding="utf-8") as f:
        f.write(PLACEHOLDER_SVG)

    with app.app_context():
        if reset:
            db.drop_all()
        db.create_all()

        if Product.query.count() > 0 and not reset:
            print("数据已存在，跳过填充（如需重建请使用 --reset）")
            return

        # 用户
        for username, email, pwd, is_admin, nickname in DEMO_USERS:
            if not User.query.filter_by(username=username).first():
                u = User(username=username, email=email, is_admin=is_admin,
                         nickname=nickname)
                u.set_password(pwd)
                db.session.add(u)
        db.session.commit()

        # 分类 + 商品
        idx = 0
        for order, (cat_name, icon, cat_desc, products) in enumerate(CATALOG):
            cat = Category.query.filter_by(name=cat_name).first()
            if not cat:
                cat = Category(name=cat_name, icon=icon, description=cat_desc,
                               sort_order=order)
                db.session.add(cat)
                db.session.commit()

            for (pname, price, orig, stock, sales, summary, desc) in products:
                image = make_svg(pname, icon, idx, upload_dir)
                db.session.add(Product(
                    name=pname, category_id=cat.id, price=price,
                    original_price=orig, stock=stock, sales=sales,
                    summary=summary, description=desc, image=image, is_active=True,
                ))
                idx += 1
        db.session.commit()

        print("=" * 46)
        print("  演示数据初始化完成")
        print("=" * 46)
        print(f"  分类：{Category.query.count()} 个")
        print(f"  商品：{Product.query.count()} 件")
        print(f"  用户：{User.query.count()} 个")
        print("-" * 46)
        print("  管理员账号：admin / admin123")
        print("  普通用户：  demo  / 123456")
        print("=" * 46)


if __name__ == "__main__":
    from app import create_app

    application = create_app(Config)
    run_seed(application, reset="--reset" in sys.argv)
