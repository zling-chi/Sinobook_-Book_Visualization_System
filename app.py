from flask import Flask, render_template, jsonify
import pymysql
import jieba
from collections import Counter
import re
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# 停用词集合
STOP_WORDS = {
    '教材', '丛书', '系列', '基础', '教程', '导论', '大学', '普通', '高等',
    '专业', '规划', '版', '二十一世纪', '21世纪', '面向', '重点', '精品',
    '实验', '实践', '指导', '理论', '应用', '研究', '技术', '概论', '编写',
    '第二', '第四版', '第三版', '下册', '课件', '综合', '课程', '学生', '新编', '活动',
    '阅读', '学习', '用书', '手册', '第六版', '基础课程', '当代', '实训', '第五版', '项目',
    '英文版', '修订版', '修订', '习题', '上册', '标准', '大学生', '习题集', '实用课程', '基于',
    '案例', '新版', '实用', '高职'
}
# 加密 session 数据
app.secret_key = 'sinobook_secret_key_123456'


# 数据库连接函数
def get_db_conn():
    return pymysql.connect(
        host='localhost', user='root', password='123456',
        db='sinobook', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor
    )


#数据可视化模块
def get_db_data():
    conn = None
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='123456',
            db='sinobook',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            # 基础统计 (确保别名是 name)
            cursor.execute(
                "SELECT publisher as name, COUNT(*) as value FROM sinobooks GROUP BY publisher ORDER BY value DESC LIMIT 10")
            pub_data = cursor.fetchall()

            cursor.execute(
                "SELECT applicable_major as name, COUNT(*) as value FROM sinobooks GROUP BY applicable_major ORDER BY value DESC LIMIT 10")
            major_data = cursor.fetchall()

            cursor.execute(
                "SELECT category as name, COUNT(*) as value FROM sinobooks GROUP BY category ORDER BY value DESC")
            cat_data = cursor.fetchall()

            # 4. 年度趋势
            cursor.execute(
                "SELECT year, COUNT(*) as count FROM sinobooks WHERE year IS NOT NULL AND year != '' GROUP BY year ORDER BY year ASC")
            year_res = cursor.fetchall()
            trend_data = {"years": [str(r['year']) for r in year_res], "counts": [r['count'] for r in year_res]}

            # 5. 词云图：获取所有书名并分词
            cursor.execute("SELECT name FROM sinobooks")
            all_names = [r['name'] for r in cursor.fetchall()]
            # 合并所有书名
            full_text = "".join(all_names)
            # 使用 jieba 分词
            words = jieba.lcut(full_text)
            # 【核心修改点】：增加停用词过滤逻辑
            filtered_words = [
                w for w in words
                if len(w) > 1  # 长度大于1（过滤掉“的”、“和”等单字）
                   and w not in STOP_WORDS  # 不在停用词列表里
                   and not w.isdigit()  # 过滤掉纯数字
            ]
            # 统计词频
            word_counts = Counter(filtered_words)
            # 提取出现频率最高的前 50 个词
            wc_data = [{"name": k, "value": v} for k, v in word_counts.most_common(150)]

            # 6. 图书价格区间统计 (柱状图数据) ---
            cursor.execute("""
                SELECT name, COUNT(*) as value FROM (
                    SELECT 
                        CASE 
                            WHEN price <= 20 THEN '0-20元'
                            WHEN price > 20 AND price <= 40 THEN '20-40元'
                            WHEN price > 40 AND price <= 60 THEN '40-60元'
                            WHEN price > 60 AND price <= 80 THEN '60-80元'
                            WHEN price > 80 AND price <= 100 THEN '80-100元'
                            ELSE '100元以上'
                        END AS name
                    FROM sinobooks 
                    WHERE price IS NOT NULL AND price > 0
                ) as temp_table
                GROUP BY name
                ORDER BY FIELD(name, '0-20元', '20-40元', '40-60元', '60-80元', '80-100元', '100元以上')
            """)
            price_range_data = cursor.fetchall()

            # 修改返回字典中的价格字段
            return {
                "publisher": pub_data,
                "major": major_data,
                "category": cat_data,
                "trend": trend_data,
                "wordcloud": wc_data,
                "price_dist": price_range_data  # 变为统计后的数组
            }
    except Exception as e:
        # 如果报错，这里会强制在控制台打印红色错误
        import traceback
        traceback.print_exc()
        return None
    finally:
        if conn: conn.close()


#  用户注册登录模块
@app.route('/register', methods=['GET', 'POST'])
# 用户注册
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        # 密码加密存储
        hashed_password = generate_password_hash(password)
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                # 检查用户名是否已存在
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    return "用户名已存在", 400

                # 插入新用户
                sql = "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)"
                cursor.execute(sql, (username, hashed_password, email))
            conn.commit()
            return redirect(url_for('login'))  # 注册成功跳到登录
        except Exception as e:
            print(f"注册失败: {e}")
            return "注册系统异常", 500
        finally:
            conn.close()
    return render_template('register.html')


# 用户登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                # 查询用户信息
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                # --- 修改点：变量名由 user 改为 db_user ---
                db_user = cursor.fetchone()
                # 使用 db_user 访问数据
                if db_user and check_password_hash(db_user['password'], password):
                    # 登录成功，记录 Session
                    session['user_id'] = db_user['id']
                    session['username'] = db_user['username']
                    # 跳转到首页
                    return redirect(url_for('index'))
                else:
                    return "用户名或密码错误", 401
        finally:
            conn.close()
    return render_template('login.html')


# 图书收藏接口
@app.route('/api/add_favorite', methods=['POST'])
def add_favorite():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "请先登录"})
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "请求数据为空"})
    book_id = data.get('book_id')
    if not book_id:
        return jsonify({"status": "error", "message": "book_id为空"})
    user_id = session['user_id']
    conn = get_db_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM favorites WHERE user_id=%s AND book_id=%s",
                (user_id, book_id)
            )
            if cursor.fetchone():
                return jsonify({"status": "error", "message": "已经收藏过"})
            cursor.execute(
                "INSERT INTO favorites (user_id, book_id) VALUES (%s, %s)",
                (user_id, book_id)
            )
            conn.commit()
            return jsonify({"status": "success"})
    except Exception as e:
        print("收藏错误:", e)
        return jsonify({"status": "error", "message": str(e)})
    finally:
        conn.close()


# 获取收藏列表接口
@app.route('/api/my_favorites')
def my_favorites():
    if 'user_id' not in session: return jsonify([])
    user_id = session['user_id']
    conn = get_db_conn()
    try:
        with conn.cursor() as cursor:
            # 使用别名 name AS book_name 解决前端 undefined 问题
            sql = """
                SELECT b.id,b.name AS book_name, b.publisher, b.price, b.author 
                FROM sinobooks b
                JOIN favorites f ON b.id = f.book_id
                WHERE f.user_id = %s
                ORDER BY f.created_at DESC
            """
            cursor.execute(sql, (user_id,))
            return jsonify(cursor.fetchall())
    finally:
        conn.close()

# 新增：图书检索接口
@app.route('/api/search')
def api_search():
    if 'user_id' not in session:
        return jsonify({"error": "unauthorized"}), 401

    keyword = request.args.get('keyword', '')
    if not keyword:
        return jsonify([])

    conn = get_db_conn()
    try:
        with conn.cursor() as cursor:
            # 1. 扩展查询字段：增加 author, isbn, applicable_major
            # 2. 扩展匹配条件：只要其中一项包含关键词即可
            sql = """
                SELECT id, name AS book_name, author, publisher, price, ISBN, 
                       applicable_major  
                FROM sinobooks 
                WHERE name LIKE %s 
                   OR author LIKE %s 
                   OR publisher LIKE %s 
                   OR ISBN LIKE %s 
                   OR applicable_major LIKE %s
                LIMIT 50
            """
            search_val = f'%{keyword}%'
            # 对应 SQL 中的 5 个 %s
            cursor.execute(sql, (search_val, search_val, search_val, search_val, search_val))
            results = cursor.fetchall()
            return jsonify(results)
    except Exception as e:
        print(f"搜索出错: {e}")
        return jsonify([]), 500
    finally:
        conn.close()


# 推荐评分算法：R = 教材分级(40%) + 价格(20%) + 年份(20%) + 相似度(20%)
def calculate_recommend_score(book, target_major, target_level):
    score = 0

    # 1. 教材分级匹配 (权重 40%) - 满分 40
    grade_level = book.get('grade_level') or ""
    if target_level and target_level in grade_level:
        score += 40

    # 2. 价格适中度 (权重 20%) - 满分 20
    try:
        price = float(str(book.get('price', '0')).replace('￥', '').strip())
        if 35 <= price <= 65:
            score += 20
        elif 20 <= price < 35 or 65 < price <= 100:
            score += 10
    except:
        score += 5

    # 3. 出版年份 (权重 20%) - 满分 20
    try:
        publish_date = str(book.get('year') or "")
        year_match = re.search(r'(\d{4})', publish_date)
        if year_match:
            year = int(year_match.group(1))
            if year >= 2024:
                score += 20
            elif year >= 2021:
                score += 15
            else:
                score += 10
    except:
        score += 5

    # 4. 文本相似度 (权重 20%) - 满分 20
    book_name = book.get('book_name') or ""
    major_attr = book.get('applicable_major') or ""
    sim_points = 0
    if target_major:
        if target_major in book_name: sim_points += 15
        if target_major in major_attr: sim_points += 5
    score += sim_points

    return score

@app.route('/api/recommend')
def api_recommend():
    major = request.args.get('major', '')
    level = request.args.get('level', '')
    conn = get_db_conn()
    try:
        with conn.cursor() as cursor:
            # 1. 初筛：先根据专业或级别拉取一批候选数据（比如500条）
            # 必须查询 grade-level (别名为 grade_level) 和 publish_date
            sql = """
                            SELECT id, name AS book_name, author, publisher, price, 
                                   applicable_major, grade_level, year 
                            FROM sinobooks 
                            WHERE applicable_major LIKE %s 
                            LIMIT 300
                        """
            cursor.execute(sql, (f'%{major}%',))
            candidates = cursor.fetchall()

            for book in candidates:
                # 确保你已经定义了 calculate_recommend_score 函数
                book['r_score'] = calculate_recommend_score(book, major, level)

                # 按评分 R 从高到低排序
            recommended_list = sorted(candidates, key=lambda x: x['r_score'], reverse=True)[:20]
            return jsonify(recommended_list)
    except Exception as e:
        print(f"推荐后端报错: {e}")
        return jsonify([]), 500
    finally:
        conn.close()

@app.route('/api/remove_favorite', methods=['POST'])
def remove_favorite():
    if 'user_id' not in session: return jsonify({"status": "error", "msg": "未登录"}), 401
    data = request.json
    conn = get_db_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM favorites WHERE user_id=%s AND book_id=%s", (session['user_id'], data.get('book_id')))
            conn.commit()
            return jsonify({"status": "success"})
    finally:
        conn.close()
# 退出登录
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/api/all_stats')
def api_all_stats():
    conn = get_db_conn()
    try:
        with conn.cursor() as cursor:
            # 1. 统计图书总数
            cursor.execute("SELECT COUNT(*) as count FROM sinobooks")
            total_books = cursor.fetchone()['count']

            # 2. 统计出版社总数
            cursor.execute("SELECT COUNT(DISTINCT publisher) as count FROM sinobooks")
            total_publishers = cursor.fetchone()['count']

            # 获取原有的图表数据 (假设你已有的逻辑在 get_db_data)
            stats_data = get_db_data()

            # 将统计数值合并到返回结果中
            stats_data['total_books'] = total_books
            stats_data['total_publishers'] = total_publishers

            return jsonify(stats_data)
    finally:
        conn.close()


# 主页路由
@app.route('/')
def index():
    # 未登录用户也可访问，模板内根据 is_logged_in 控制功能显示
    is_logged_in = 'user_id' in session
    username = session.get('username', '')
    return render_template('index.html', is_logged_in=is_logged_in, username=username)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
