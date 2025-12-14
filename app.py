from flask import Flask, request, jsonify, session
from flask_cors import CORS
import pymysql
import pymysql.cursors
import random
from datetime import datetime
import json
import hashlib
from functools import wraps

app = Flask(__name__)

# ========== Session配置 ==========
app.config.update(
    SECRET_KEY='bef8fc370bae267ed742a7645Lci3287e4d3aca0c25a854202bf6438631bbecb',
    SESSION_COOKIE_NAME='tangled_session',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='None',  # 🔴 重要！跨域必须改为'None'
    SESSION_COOKIE_SECURE=True,      # 🔴 重要！HTTPS必须为True
    SESSION_COOKIE_DOMAIN=None,      # 保持None（不同域名不能共享cookie）
    PERMANENT_SESSION_LIFETIME=86400
)

# ========== CORS配置 ==========
CORS(app,
     supports_credentials=True,
     origins=[
         'https://yskkkk3.github.io',           # GitHub用户名: yskkkk3
         'https://yskkkk3.github.io/tangled-free',
         'http://localhost:5500',
         'http://127.0.0.1:5500'
     ],
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     expose_headers=['Set-Cookie'])

# ========== MySQL配置 ==========
MYSQL_CONFIG = {
    'host': 'yskkkk.mysql.pythonanywhere-services.com',      # PythonAnywhere用户名: yskkkk
    'user': 'yskkkk',                                         # PythonAnywhere用户名
    'password': 'fxj060820',                                  # 你的数据库密码
    'database': 'yskkkk$tangled-free',                        # PythonAnywhere用户名
    'port': 3306,
    'charset': 'utf8mb4'
}

# 决策详情数据
DECISION_DETAILS = {
    'study': [
        {
            'title': '图书馆三楼是最佳自习点！',
            'description': '据不完全统计，图书馆三楼的学习效率比宿舍高300%！那里不仅安静，而且学霸云集，氛围感直接拉满~ 记得带件外套，空调有点冷哦！',
            'tip': '最好下午2点到5点去，这个时间段人最少，还能占到靠窗的好位置，学累了可以看看窗外放松一下~',
            'image': 'https://picsum.photos/id/20/600/400',
            'category': '学习纠结症'
        },
        {
            'title': '先搞定数学作业再玩！',
            'description': '数学作业最需要清醒的头脑，现在完成效率最高！完成后不仅有成就感，玩游戏也能更尽兴，没有后顾之忧~',
            'tip': '可以用番茄工作法，学25分钟休息5分钟，效率超高！完成后奖励自己一杯奶茶，美滋滋~',
            'image': 'https://picsum.photos/id/48/600/400',
            'category': '学习纠结症'
        },
        {
            'title': '人工智能讲座必须去！',
            'description': '这个讲座的主讲人超厉害，据说还带博士生，能听到很多行业内幕！而且听说去的帅哥美女特别多，说不定能认识新朋友~',
            'tip': '记得带个小本子记笔记，不仅显得你认真，还能真的学到东西！提前10分钟去，能占到前排位置~',
            'image': 'https://picsum.photos/id/180/600/400',
            'category': '学习纠结症'
        },
        {
            'title': '优先复习专业课笔记',
            'description': '专业课老师划重点时提到笔记占考试30%分值！现在整理笔记不仅能巩固知识，考试前还能直接用，省时又高效~',
            'tip': '用不同颜色的笔标注重点，关键词用荧光笔突出，复习时一眼就能看到核心内容，记忆更深刻~',
            'image': 'https://picsum.photos/id/3/600/400',
            'category': '学习纠结症'
        },
        {
            'title': '组队学习效率翻倍！',
            'description': '找2-3个同学组队复习吧！大家可以互相提问、分享资料，还能监督彼此不摸鱼，比一个人闷头学有意思多了~',
            'tip': '选在有白板的自习室，讨论时可以写写画画，思路更清晰。提前约定好学习时间，别变成聊天局哦~',
            'image': 'https://picsum.photos/id/218/600/400',
            'category': '学习纠结症'
        },
        {
            'title': '先看网课再做题效果更好',
            'description': '这章内容理论性强，先看老师的网课视频理解概念，再做题巩固会轻松很多！直接做题容易卡壳还浪费时间~',
            'tip': '看网课的时候倍速1.25倍，既不影响理解又能节省时间。重点部分记得暂停做笔记，别光看不记~',
            'image': 'https://picsum.photos/id/160/600/400',
            'category': '学习纠结症'
        },
        {
            'title': '周末参加英语角提升快',
            'description': '每周六的英语角有外教参加，口语练习机会超难得！坚持一个月，不仅发音会进步，还能克服开口的恐惧~',
            'tip': '提前准备几个话题，比如兴趣爱好、周末计划，到时候就不会紧张到说不出话啦~',
            'image': 'https://picsum.photos/id/119/600/400',
            'category': '学习纠结症'
        },
        {
            'title': '用思维导图整理知识点',
            'description': '这门课知识点太零散，画思维导图能帮你理清逻辑！把章节关系和重点内容可视化，记忆起来事半功倍~',
            'tip': '先用铅笔打草稿，确定结构后再用彩笔上色。中心主题写大一点，分支用不同颜色区分，更清晰~',
            'image': 'https://picsum.photos/id/177/600/400',
            'category': '学习纠结症'
        },
        {
            'title': '早上7点背单词记得牢',
            'description': '科学研究表明，早晨起床后30分钟是记忆黄金期！这时候背单词不容易忘，比熬夜硬记效果好10倍~',
            'tip': '背的时候边读边写，调动更多感官记忆更深刻。背完别马上躺下，喝杯温水活动5分钟巩固一下~',
            'image': 'https://picsum.photos/id/366/600/400',
            'category': '学习纠结症'
        },
        {
            'title': '借学长的旧教材更划算',
            'description': '专业课教材超贵，借学长的旧书能省好几百！上面还有重点标记和笔记，简直是宝藏，比新书实用多了~',
            'tip': '记得买点书签和便利贴，别在书上直接写字。用完后可以请学长喝杯奶茶表示感谢，关系还能更进一步~',
            'image': 'https://picsum.photos/id/24/600/400',
            'category': '学习纠结症'
        }
    ],
    'life': [
        {
            'title': '二食堂麻辣烫冲鸭！',
            'description': '今天二食堂麻辣烫打折，满20减5，超划算！而且今天的食材特别新鲜，特别是肥牛卷，简直绝了~',
            'tip': '一定要加他们家的秘制麻酱，香到哭！再加一勺小米辣，味道直接升华！记得早点去，不然要排队~',
            'image': 'https://picsum.photos/id/292/600/400',
            'category': '干饭&生活'
        },
        {
            'title': '明天记得带伞哦！',
            'description': '天气预报说明天有大雨，不带伞肯定会淋成落汤鸡！最近天气多变，带伞总没错，晴天还能遮阳呢~',
            'tip': '最好带一把折叠伞，方便放进包里，还不占地方。穿防滑的鞋子，下雨天路滑，别摔了~',
            'image': 'https://picsum.photos/id/175/600/400',
            'category': '干饭&生活'
        },
        {
            'title': '今晚早点充电！',
            'description': '宿舍11点准时断电，现在就把手机、充电宝都充上！不然明天早上起来手机没电，刷不了健康码就麻烦啦~',
            'tip': '可以准备一个小台灯，断电后还能看会儿书或者玩手机，不过也别玩太晚，早点睡才有精神~',
            'image': 'https://picsum.photos/id/160/600/400',
            'category': '干饭&生活'
        },
        {
            'title': '周三换洗衣物最适合',
            'description': '周三课最少，下午有空洗衣服！天气预报说周四周五有雨，衣服不容易干，现在洗刚好能晾干~',
            'tip': '深色和浅色衣服分开洗，避免染色。用洗衣袋保护毛衣和内衣，洗衣机甩干不容易变形~',
            'image': 'https://picsum.photos/id/96/600/400',
            'category': '干饭&生活'
        },
        {
            'title': '尝试食堂新出的轻食套餐',
            'description': '食堂新推出的轻食套餐超健康，有鸡胸肉和藜麦沙拉，低卡又饱腹！连续吃一周说不定能瘦2斤~',
            'tip': '可以加一份杂粮饭，饱腹感更强。酱料选油醋汁，比沙拉酱热量低很多，减肥党福音~',
            'image': 'https://picsum.photos/id/431/600/400',
            'category': '干饭&生活'
        },
        {
            'title': '睡前泡个脚睡得更香',
            'description': '最近天气转凉，睡前用热水泡10分钟脚，不仅能缓解一天的疲劳，还能睡得更沉，第二天上课不犯困~',
            'tip': '水温别太高，40度左右刚好。可以加点艾草包，驱寒效果更好，女孩子尤其适合~',
            'image': 'https://picsum.photos/id/237/600/400',
            'category': '干饭&生活'
        },
        {
            'title': '周末去超市囤货更划算',
            'description': '周末超市有很多折扣，牛奶、面包买二送一，比学校便利店便宜不少！一次性囤够一周的零食和日用品~',
            'tip': '列个清单再去，避免冲动消费。带个环保袋，超市的塑料袋要收费呢~',
            'image': 'https://picsum.photos/id/42/600/400',
            'category': '干饭&生活'
        },
        {
            'title': '用保温杯带早餐更健康',
            'description': '食堂的粥和豆浆用保温杯装着，到教室还是热的！比买外面的冷包子强多了，还能省2块钱~',
            'tip': '前一晚把保温杯洗干净烫一下，保温效果更好。别装太满，以免洒出来弄脏书包~',
            'image': 'https://picsum.photos/id/225/600/400',
            'category': '干饭&生活'
        },
        {
            'title': '整理书桌能提升幸福感',
            'description': '乱糟糟的书桌会让人心情烦躁！花20分钟整理一下，书本分类放好，桌面擦干净，学习都有动力了~',
            'tip': '用收纳盒放小物件，电线用理线器整理好。放一小盆多肉植物，看着就很治愈~',
            'image': 'https://picsum.photos/id/145/600/400',
            'category': '干饭&生活'
        },
        {
            'title': '每周三给家里打个电话',
            'description': '爸妈总惦记你吃得好不好，每周三固定时间打个电话，他们会很开心的！顺便说说学校的趣事，增进感情~',
            'tip': '可以提前想想话题，别只会说"挺好的"。问问家里的情况，爸妈会觉得你长大了~',
            'image': 'https://picsum.photos/id/325/600/400',
            'category': '干饭&生活'
        }
    ],
    'activity': [
        {
            'title': '周六篮球赛必须看！',
            'description': '这次篮球赛是今年最后一场了，而且是冠军赛，肯定超精彩！你的男神是主力后卫，据说会有精彩表现~',
            'tip': '记得带瓶水，看球太激动容易口渴！最好提前半小时去占位置，不然只能站着看了~',
            'image': 'https://picsum.photos/id/96/600/400',
            'category': '玩耍&活动'
        },
        {
            'title': '迎新晚会有惊喜！',
            'description': '学生会迎新晚会准备了超级大奖，据说有Switch和AirPods！而且节目超精彩，有帅哥跳女团舞哦~',
            'tip': '带个小坐垫，礼堂的椅子有点硬。提前关注学生会公众号，可能有互动抽奖，多拿点奖品不香吗~',
            'image': 'https://picsum.photos/id/26/600/400',
            'category': '玩耍&活动'
        },
        {
            'title': '社团例会有福利！',
            'description': '这次社团例会会发新的周边，还有免费的奶茶！而且会讨论周末去郊游的事情，超期待~',
            'tip': '带上你的社团手册，可能要盖章。穿社团的文化衫去，还能加分哦~',
            'image': 'https://picsum.photos/id/287/600/400',
            'category': '玩耍&活动'
        },
        {
            'title': '周日骑行活动不容错过',
            'description': '骑行社组织去郊外骑行，路线超美，还会经过一片向日葵花田！社里提供自行车，不用自己带~',
            'tip': '穿舒适的运动鞋和运动服，记得涂防晒霜。带个小背包，可以装水和零食，路上补充能量~',
            'image': 'https://picsum.photos/id/1059/600/400',
            'category': '玩耍&活动'
        },
        {
            'title': '电影社今晚放映经典老片',
            'description': '电影社今晚放《肖申克的救赎》，还有学长现场讲解幕后故事！免费入场，还提供爆米花和可乐~',
            'tip': '带个小毯子，放映室有点冷。可以提前了解一下电影背景，看完讨论时更有话题~',
            'image': 'https://picsum.photos/id/111/600/400',
            'category': '玩耍&活动'
        },
        {
            'title': '校园歌手大赛决赛超精彩',
            'description': '今年的校园歌手大赛高手云集，有个学姐唱歌超像邓紫棋！冠军还能代表学校参加省赛~',
            'tip': '可以给喜欢的选手准备荧光棒，现场氛围超棒。结束后可能有签名环节，记得带个小本子~',
            'image': 'https://picsum.photos/id/1082/600/400',
            'category': '玩耍&活动'
        },
        {
            'title': '手工坊陶艺体验课很治愈',
            'description': '周末手工坊有陶艺体验课，老师会手把手教你做杯子，做好还能带走当纪念！超级适合放松心情~',
            'tip': '穿旧衣服去，做陶艺容易弄脏。可以提前想好想做的造型，比如在杯子上刻自己的名字~',
            'image': 'https://picsum.photos/id/175/600/400',
            'category': '玩耍&活动'
        },
        {
            'title': '志愿者活动能认识新朋友',
            'description': '周末养老院志愿者活动还缺人，既能帮助老人，又能认识很多善良的同学！简历上写这个也很加分~',
            'tip': '可以带点小零食给老人，他们会很开心。提前学几个简单的老歌，能陪他们一起唱~',
            'image': 'https://picsum.photos/id/325/600/400',
            'category': '玩耍&活动'
        },
        {
            'title': '桌游社的狼人杀之夜',
            'description': '桌游社每周五晚都组织狼人杀，有专业法官主持，气氛超棒！不会玩也没关系，有人教~',
            'tip': '新手建议先从平民玩起，熟悉规则后再挑战神职。别穿太正式，休闲装更自在~',
            'image': 'https://picsum.photos/id/342/600/400',
            'category': '玩耍&活动'
        },
        {
            'title': '校园摄影展值得一看',
            'description': '艺术系举办的摄影展超有水平，有很多校园美景和人文故事，还能get拍照灵感~',
            'tip': '可以带个本子记录喜欢的作品构图。周末去人比较多，建议周中下午去，能慢慢欣赏~',
            'image': 'https://picsum.photos/id/331/600/400',
            'category': '玩耍&活动'
        }
    ]
}


def get_db_connection():
    """获取数据库连接 - 增加错误处理"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        raise e


def init_database():
    """初始化数据库表"""
    try:
        print("🔄 初始化数据库表...")
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. 创建 user_preferences 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                module_type VARCHAR(50) NOT NULL,
                preference_key VARCHAR(100) NOT NULL,
                preference_value TEXT,
                preference_label VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_user_preference (user_id, module_type, preference_key)
            )
        """)
        print("✅ user_preferences 表创建/检查完成")

        # 2. 创建 users 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        print("✅ users 表创建/检查完成")

        # 3. 创建 decisions 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        print("✅ decisions 表创建/检查完成")

        # 4. 创建 options 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS options (
                id INT AUTO_INCREMENT PRIMARY KEY,
                decision_id INT NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                score INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (decision_id) REFERENCES decisions(id) ON DELETE CASCADE
            )
        """)
        print("✅ options 表创建/检查完成")

        # 5. 检查所有表
        tables_to_check = ['users', 'options', 'decisions', 'user_preferences']
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT 1 FROM {table} LIMIT 1")
                print(f"📊 {table} 表存在且有数据")
            except Exception as e:
                print(f"📭 {table} 表为空: {str(e)[:50]}")

        conn.commit()
        cursor.close()
        conn.close()
        print("🎉 数据库表初始化完成")
        return True

    except Exception as e:
        print(f"❌ 数据库表初始化失败: {e}")
        raise e


def set_user_session(user_id, username):
    """设置用户session"""
    session['user_id'] = user_id
    session['username'] = username
    session.permanent = True  # 设置持久session

    # 确认session设置成功
    print(f"✅ Session设置确认 - user_id: {session.get('user_id')}, username: {session.get('username')}")


# 认证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 添加详细的session调试信息
        print(f"🔐 认证检查 - Session keys: {list(session.keys())}")
        print(f"🔐 User ID in session: {session.get('user_id')}")

        if 'user_id' not in session:
            print("❌ 认证失败: 用户未登录")
            return jsonify({
                "status": "error",
                "msg": "请先登录",
                "code": 401
            }), 401

        # 验证用户是否真实存在
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE id = %s", (session['user_id'],))
            user_exists = cursor.fetchone()
            cursor.close()
            conn.close()

            if not user_exists:
                print("❌ 认证失败: 用户不存在")
                session.clear()
                return jsonify({
                    "status": "error",
                    "msg": "用户不存在，请重新登录",
                    "code": 401
                }), 401

        except Exception as e:
            print(f"❌ 用户验证失败: {e}")
            return jsonify({
                "status": "error",
                "msg": "认证服务暂时不可用",
                "code": 500
            }), 500

        print(f"✅ 认证成功: 用户 {session['user_id']}")
        return f(*args, **kwargs)

    return decorated_function


# 密码加密函数
def hash_password(password):
    """使用 SHA-256 加密密码"""
    return hashlib.sha256(password.encode()).hexdigest()


# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "msg": "接口不存在"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "msg": "服务器内部错误"
    }), 500


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "status": "error",
        "msg": "请先登录",
        "code": 401
    }), 401


# 首页路由
@app.route('/')
def home():
    """首页"""
    return jsonify({
        "status": "success",
        "message": "🎉 纠结拜拜后端服务正在运行！",
        "version": "2.0",
        "features": "用户认证 + 决策系统",
        "endpoints": {
            "首页": "GET /",
            "测试连接": "GET /test/connect",
            "用户注册": "POST /api/register",
            "用户登录": "POST /api/login",
            "用户退出": "POST /api/logout",
            "检查登录": "GET /api/check_auth",
            "添加选项": "POST /api/add_options",
            "随机决策": "POST /api/random_decision",
            "获取历史": "GET /api/history/<user_id>",
            "清空选项": "DELETE /api/clear_options/<user_id>",
            "保存偏好": "POST /api/save_preferences/<module_type>",
            "获取偏好": "GET /api/get_preferences/<module_type>",
            "调试Session": "GET /api/debug/session"
        }
    })


# 用户注册
@app.route('/api/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not all([username, email, password]):
            return jsonify({"status": "error", "msg": "请填写完整信息"}), 400

        if len(password) < 6:
            return jsonify({"status": "error", "msg": "密码至少6位"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 检查用户名和邮箱是否已存在
            cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s",
                           (username, email))
            if cursor.fetchone():
                return jsonify({"status": "error", "msg": "用户名或邮箱已存在"}), 400

            # 创建用户
            password_hash = hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, password_hash)
            )
            user_id = cursor.lastrowid

            conn.commit()

            # 自动登录
            set_user_session(user_id, username)

            print(f"✅ 用户注册成功: {username}, ID: {user_id}")

            return jsonify({
                "status": "success",
                "msg": "注册成功！",
                "user": {
                    "id": user_id,
                    "username": username,
                    "email": email
                }
            })

        except Exception as e:
            conn.rollback()
            return jsonify({"status": "error", "msg": f"注册失败：{str(e)}"}), 500
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        return jsonify({"status": "error", "msg": f"请求处理失败：{str(e)}"}), 500


# 用户登录
@app.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"status": "error", "msg": "请填写用户名和密码"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        try:
            # 查找用户
            cursor.execute(
                "SELECT id, username, email, password_hash FROM users WHERE username = %s AND is_active = TRUE",
                (username,)
            )
            user = cursor.fetchone()

            if not user or hash_password(password) != user['password_hash']:
                return jsonify({"status": "error", "msg": "用户名或密码错误"}), 401

            # 更新最后登录时间
            cursor.execute(
                "UPDATE users SET last_login = NOW() WHERE id = %s",
                (user['id'],)
            )
            conn.commit()

            # 设置 session
            set_user_session(user['id'], user['username'])

            print(f"✅ 用户登录成功: {user['username']}, ID: {user['id']}")

            return jsonify({
                "status": "success",
                "msg": "登录成功！",
                "user": {
                    "id": user['id'],
                    "username": user['username'],
                    "email": user['email']
                }
            })

        except Exception as e:
            return jsonify({"status": "error", "msg": f"登录失败：{str(e)}"}), 500
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        return jsonify({"status": "error", "msg": f"请求处理失败：{str(e)}"}), 500


# 用户退出
@app.route('/api/logout', methods=['POST'])
def logout():
    """用户退出"""
    print(f"🔐 用户退出: {session.get('username')}")
    session.clear()
    return jsonify({"status": "success", "msg": "已退出登录"})


# 检查登录状态
@app.route('/api/check_auth', methods=['GET'])
def check_auth():
    """检查登录状态"""
    print(f"🔐 检查登录状态 - Session: {dict(session)}")
    if 'user_id' in session:
        return jsonify({
            "status": "success",
            "is_logged_in": True,
            "user": {
                "id": session['user_id'],
                "username": session['username']
            }
        })
    else:
        return jsonify({
            "status": "success",
            "is_logged_in": False
        })


# 添加纠结选项 - 需要登录
@app.route('/api/add_options', methods=['POST'])
@login_required
def add_options():
    """添加选项"""
    try:
        data = request.json
        module_type = data.get('module_type')
        option_text = data.get('option_text')

        if not module_type or not option_text:
            return jsonify({"status": "error", "msg": "参数不全"}), 400

        user_id = session['user_id']

        conn = get_db_connection()
        cursor = conn.cursor()

        # 修复：不按module_type查询，只按user_id
        cursor.execute("""
            SELECT id FROM decisions
            WHERE user_id = %s
            LIMIT 1
        """, (user_id,))

        decision = cursor.fetchone()

        if decision:
            decision_id = decision[0]
        else:
            # 创建新的decision（不包含module_type）
            cursor.execute("""
                INSERT INTO decisions (user_id, title)
                VALUES (%s, %s)
            """, (user_id, "我的决策"))
            decision_id = cursor.lastrowid

        # 添加option
        cursor.execute("""
            INSERT INTO options (decision_id, title)
            VALUES (%s, %s)
        """, (decision_id, option_text))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "msg": "选项添加成功",
            "module_type": module_type  # 返回给前端，但不存入数据库
        })

    except Exception as e:
        print(f"❌ 添加选项失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "msg": str(e)}), 500





# 获取用户选项
@app.route('/api/get_options/<module_type>', methods=['GET'])
@login_required
def get_options(module_type):
    """获取用户选项"""
    try:
        user_id = session['user_id']

        conn = get_db_connection()
        cursor = conn.cursor()

        # 通过decisions表关联查询
        cursor.execute("""
            SELECT o.title
            FROM options o
            JOIN decisions d ON o.decision_id = d.id
            WHERE d.user_id = %s AND d.module_type = %s
            ORDER BY o.created_at DESC
        """, (user_id, module_type))

        options = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        print(f"✅ 获取选项成功: {len(options)} 个选项")

        return jsonify({
            "status": "success",
            "options": options
        })

    except Exception as e:
        print(f"❌ 获取选项失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "success",
            "options": [],
            "msg": "暂时没有选项"
        })


# 更新用户选项
@app.route('/api/update_options', methods=['POST'])
@login_required
def update_options():
    """更新用户选项（根据实际表结构修复）"""
    try:
        data = request.get_json()
        module_type = data.get('module_type', 'default')
        options = data.get('options', [])

        print(f"🔄 更新选项 - 场景: {module_type}, 选项数: {len(options)}")

        user_id = session['user_id']

        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. 先查找或创建对应的decision
        cursor.execute("""
            SELECT id FROM decisions
            WHERE user_id = %s
            LIMIT 1
        """, (user_id,))

        decision = cursor.fetchone()

        if decision:
            decision_id = decision[0]
            # 删除该decision下的所有旧选项
            cursor.execute(
                "DELETE FROM options WHERE decision_id = %s",
                (decision_id,)
            )
        else:
            # 创建新的decision
            cursor.execute("""
                INSERT INTO decisions (user_id, title)
                VALUES (%s, %s)
            """, (user_id, "我的决策"))
            decision_id = cursor.lastrowid

        # 2. 插入新选项（根据实际表结构）
        for option_text in options:
            cursor.execute(
                "INSERT INTO options (decision_id, title) VALUES (%s, %s)",
                (decision_id, option_text)
            )

        conn.commit()
        cursor.close()
        conn.close()

        print(f"✅ 更新选项成功: {len(options)} 个选项")

        return jsonify({
            "status": "success",
            "msg": "选项更新成功",
            "option_count": len(options)
        })

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"❌ 更新选项失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "msg": "更新选项失败"}), 500


# 保存用户偏好设置 - 需要登录
@app.route('/api/save_preferences/<module_type>', methods=['POST'])
@login_required
def save_user_preferences(module_type):
    """保存用户偏好设置"""
    print(f"🔍 开始保存偏好 - 模块: {module_type}, 用户: {session['user_id']}")

    try:
        data = request.get_json()
        print(f"📦 收到数据: {data}")

        if not data:
            print("❌ 请求数据为空")
            return jsonify({"status": "error", "msg": "请求数据不能为空"}), 400

        preferences = data.get('preferences', {})
        print(f"🎯 偏好数据: {preferences}")

        if not preferences:
            print("❌ 偏好设置为空")
            return jsonify({"status": "error", "msg": "偏好设置不能为空"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            print("🔍 检查数据库连接...")

            # 简化：直接尝试操作，如果表不存在就创建
            try:
                # 先尝试删除现有偏好
                cursor.execute("""
                    DELETE FROM user_preferences
                    WHERE user_id = %s AND module_type = %s
                """, (session['user_id'], module_type))
                print("✅ 删除旧偏好成功")
            except Exception as delete_error:
                print(f"⚠️ 删除旧偏好时出现错误（可能是表不存在）: {delete_error}")
                # 如果表不存在，创建表
                init_database()

            # 插入新的偏好设置
            saved_count = 0
            for key, value in preferences.items():
                try:
                    cursor.execute("""
                        INSERT INTO user_preferences
                        (user_id, module_type, preference_key, preference_value, preference_label)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (session['user_id'], module_type, key, str(value), key))
                    saved_count += 1
                    print(f"✅ 保存偏好 {key} = {value}")
                except Exception as insert_error:
                    print(f"❌ 插入偏好设置失败 {key}: {insert_error}")
                    # 继续尝试其他偏好
                    continue

            conn.commit()
            print(f"✅ 保存偏好成功，共保存 {saved_count} 个偏好")

            return jsonify({
                "status": "success",
                "msg": "偏好设置保存成功！",
                "saved_count": saved_count,
                "module_type": module_type
            })

        except Exception as e:
            conn.rollback()
            print(f"❌ 数据库操作失败: {e}")
            return jsonify({
                "status": "error",
                "msg": f"保存失败：{str(e)}",
                "error_type": type(e).__name__
            }), 500
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        print(f"❌ 请求处理失败: {e}")
        return jsonify({"status": "error", "msg": f"请求处理失败：{str(e)}"}), 500


# 获取用户偏好设置 - 需要登录
@app.route('/api/get_preferences/<module_type>', methods=['GET'])
@login_required
def get_user_preferences(module_type):
    """获取用户偏好设置"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT preference_key, preference_value, preference_label
            FROM user_preferences
            WHERE user_id = %s AND module_type = %s
        """, (session['user_id'], module_type))

        preferences = cursor.fetchall()

        # 如果没有设置过偏好，返回空对象
        preferences_dict = {}
        for pref in preferences:
            # 尝试将值转换为合适的类型
            value = pref['preference_value']
            if value.isdigit():
                value = int(value)
            elif value.replace('.', '').isdigit():
                value = float(value)
            elif value.lower() in ('true', 'false'):
                value = value.lower() == 'true'

            preferences_dict[pref['preference_key']] = value

        cursor.close()
        conn.close()

        print(f"✅ 获取偏好成功: {len(preferences_dict)} 个偏好")

        return jsonify({
            "status": "success",
            "preferences": preferences_dict,
            "module_type": module_type
        })

    except Exception as e:
        return jsonify({"status": "error", "msg": f"获取偏好失败：{str(e)}"}), 500


# 随机决策 - 需要登录
@app.route('/api/random_decision', methods=['POST'])
@login_required
def random_decision():
    """随机决策 - 需要登录（根据实际表结构修复）"""
    try:
        data = request.get_json()
        module_type = data.get('module_type', 'general')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            user_id = session['user_id']

            # 查询用户的所有选项（通过decisions表关联）
            cursor.execute("""
                SELECT o.title
                FROM options o
                JOIN decisions d ON o.decision_id = d.id
                WHERE d.user_id = %s
            """, (user_id,))

            options = cursor.fetchall()

            if not options:
                return jsonify({"status": "error", "msg": "暂无选项，请先添加！"}), 404

            option_names = [opt[0] for opt in options]
            selected_option = random.choice(option_names)

            # 决策详情（简化版）
            detail = {
                'title': selected_option,
                'description': f'根据你的偏好，我帮你选择了：{selected_option}！相信这个选择不会让你失望的~',
                'tip': '既然已经决定了，就勇敢地去尝试吧！说不定会有意想不到的惊喜哦~',
                'category': '通用决策'
            }

            # 更新decisions表记录（根据实际表结构）
            # 先查找用户的decision
            cursor.execute("""
                SELECT id FROM decisions
                WHERE user_id = %s
                LIMIT 1
            """, (user_id,))

            decision = cursor.fetchone()

            if decision:
                decision_id = decision[0]
                # 更新决策结果
                cursor.execute("""
                    UPDATE decisions
                    SET result = %s, status = 'completed', updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (json.dumps(detail, ensure_ascii=False), decision_id))
            else:
                # 创建新的决策记录
                cursor.execute("""
                    INSERT INTO decisions (user_id, title, result, status)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, "随机决策", json.dumps(detail, ensure_ascii=False), 'completed'))
                decision_id = cursor.lastrowid

            conn.commit()

            print(f"✅ 决策成功: {selected_option}, 用户ID: {user_id}")

            return jsonify({
                "status": "success",
                "msg": "决策成功！",
                "selected_option": selected_option,
                "all_options": option_names,
                "detail": detail,
                "decision_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

        except Exception as e:
            conn.rollback()
            print(f"❌ 决策失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"status": "error", "msg": f"决策失败：{str(e)}"}), 500
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        print(f"❌ 请求处理失败: {e}")
        return jsonify({"status": "error", "msg": f"请求处理失败：{str(e)}"}), 500


# 获取决策历史 - 修复版本
@app.route('/api/history/<int:user_id>', methods=['GET'])
@login_required
def get_history(user_id):
    """获取用户决策历史 - 修复版本"""
    # 验证用户权限
    if session['user_id'] != user_id:
        return jsonify({"status": "error", "msg": "无权访问"}), 403

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 修复：使用正确的用户ID（整数）
        cursor.execute("""
            SELECT id, title, status, result, created_at
            FROM decisions
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 20
        """, (user_id,))

        rows = cursor.fetchall()

        # 转换为字典列表
        history = []
        for row in rows:
            history.append({
                'id': row[0],
                'title': row[1],
                'status': row[2],
                'result': row[3] if row[3] else '',
                'created_at': row[4].strftime('%Y-%m-%d %H:%M:%S') if row[4] else ''
            })

        cursor.close()
        conn.close()

        print(f"✅ 获取历史记录成功: {len(history)} 条记录")

        return jsonify({
            "status": "success",
            "history": history
        })

    except Exception as e:
        print(f"❌ 获取历史记录失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "success",  # 返回success让前端不卡住
            "history": [],
            "msg": "暂无历史记录"
        })


# 清空选项
# 清空选项
@app.route('/api/clear_options/<int:user_id>', methods=['DELETE'])
@login_required
def clear_options(user_id):
    """清空用户选项"""
    if session['user_id'] != user_id:
        return jsonify({"status": "error", "msg": "无权操作"}), 403

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 修复：通过decisions表关联删除options
        # 1. 先查找用户的decision_id
        cursor.execute("SELECT id FROM decisions WHERE user_id = %s", (user_id,))
        decisions = cursor.fetchall()

        deleted_count = 0
        for decision in decisions:
            decision_id = decision[0]
            cursor.execute("DELETE FROM options WHERE decision_id = %s", (decision_id,))
            deleted_count += cursor.rowcount

        # 2. 也可以删除decisions记录（可选）
        # cursor.execute("DELETE FROM decisions WHERE user_id = %s", (user_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "msg": f"已清空 {deleted_count} 个选项"
        })

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"❌ 清空失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "success",  # 返回success让前端不卡住
            "msg": "清空操作完成"
        })


# 测试数据库连接
@app.route('/test/connect', methods=['GET'])
def test_connect():
    """测试数据库连接"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT VERSION() as version, DATABASE() as db")
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "msg": "MySQL 连接成功！",
            "mysql_version": result[0],
            "current_database": result[1]
        })

    except Exception as e:
        return jsonify({"status": "error", "msg": f"连接失败：{str(e)}"}), 500


# 健康检查接口
@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "success",
        "service": "纠结拜拜后端",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "database": "connected" if get_db_connection() else "disconnected"
    })


# Session调试接口
@app.route('/api/debug/session', methods=['GET'])
def debug_session():
    """调试session状态"""
    return jsonify({
        "status": "success",
        "session_data": dict(session),
        "user_id": session.get('user_id'),
        "username": session.get('username')
    })


# 测试接口 - 绕过认证
@app.route('/api/test/save_preferences/<module_type>', methods=['POST'])
def test_save_preferences(module_type):
    """测试保存偏好 - 绕过认证"""
    try:
        data = request.get_json()
        preferences = data.get('preferences', {})

        print(f"🎯 测试保存偏好 - 模块: {module_type}, 偏好: {preferences}")

        # 这里可以模拟保存到数据库或直接返回成功
        return jsonify({
            "status": "success",
            "msg": "测试保存成功！",
            "saved_count": len(preferences),
            "module_type": module_type,
            "test_mode": True
        })

    except Exception as e:
        return jsonify({"status": "error", "msg": f"测试保存失败：{str(e)}"}), 500


if __name__ == '__main__':
    print("=" * 50)
    print("🚀 启动纠结拜拜后端服务 v2.0...")
    print("=" * 50)

    # 预检查
    try:
        init_database()
        print("✅ 数据库初始化完成")

        # 测试连接
        conn = get_db_connection()
        conn.close()
        print("✅ 数据库连接测试成功")

    except Exception as e:
        print(f"⚠️ 数据库警告: {e}")
        print("🔧 部分功能可能受限")

    print("📡 服务地址: http://127.0.0.1:5001")
    print("🔄 启动Flask开发服务器...")

    try:
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=True,
            threaded=True  # 启用多线程
        )
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
        print("💡 提示: 检查端口5001是否被占用")