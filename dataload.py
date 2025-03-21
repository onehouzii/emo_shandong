import requests
import json
import time
from datetime import datetime
import pandas as pd
from flask import Flask, request
import webbrowser
from threading import Thread, Event
import sqlite3
from snownlp import SnowNLP
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 微博 API 配置
APP_KEY = '2740570086'
APP_SECRET = '5c9cdc3b9f6bc0f372e47e25d95f7375'
REDIRECT_URI = 'http://127.0.0.1:8080/callback'
OAUTH_URL = f'https://api.weibo.com/oauth2/authorize?client_id={APP_KEY}&redirect_uri={REDIRECT_URI}&response_type=code'

# 山东省主要城市坐标
SHANDONG_CITIES = {
    '济南': {'lat': 36.675807, 'lon': 117.000923},
    '青岛': {'lat': 36.082982, 'lon': 120.355173},
    '淄博': {'lat': 36.814939, 'lon': 118.047648},
    '枣庄': {'lat': 34.856424, 'lon': 117.557964},
    '东营': {'lat': 37.434564, 'lon': 118.66471},
    '烟台': {'lat': 37.539297, 'lon': 121.391382},
    '潍坊': {'lat': 36.70925, 'lon': 119.107078},
    '济宁': {'lat': 35.415393, 'lon': 116.587245},
    '泰安': {'lat': 36.194968, 'lon': 117.129063},
    '威海': {'lat': 37.509691, 'lon': 122.116394},
    '日照': {'lat': 35.428588, 'lon': 119.461208},
    '临沂': {'lat': 35.065282, 'lon': 118.326443},
    '德州': {'lat': 37.453968, 'lon': 116.307428},
    '聊城': {'lat': 36.456013, 'lon': 115.980367},
    '滨州': {'lat': 37.383542, 'lon': 118.016974},
    '菏泽': {'lat': 35.246531, 'lon': 115.469381}
}

# 全局变量
access_token = None
auth_event = Event()  # 用于同步授权状态

# 初始化 Flask 应用
app = Flask(__name__)

def init_database():
    """初始化数据库"""
    conn = sqlite3.connect('weibo_data.db')
    c = conn.cursor()
    
    # 创建 POI 表
    c.execute('''CREATE TABLE IF NOT EXISTS pois
                 (id TEXT PRIMARY KEY, 
                  title TEXT,
                  address TEXT,
                  city TEXT,
                  latitude REAL,
                  longitude REAL,
                  checkin_num INTEGER,
                  created_at TIMESTAMP)''')
    
    # 创建评论表
    c.execute('''CREATE TABLE IF NOT EXISTS comments
                 (id TEXT PRIMARY KEY,
                  poi_id TEXT,
                  content TEXT,
                  created_at TIMESTAMP,
                  sentiment_score REAL,
                  FOREIGN KEY (poi_id) REFERENCES pois(id))''')
    
    conn.commit()
    conn.close()

@app.route('/callback')
def callback():
    """处理 OAuth 回调"""
    global access_token
    code = request.args.get('code')
    logging.info(f"收到授权码: {code}")
    
    # 获取访问令牌
    token_url = 'https://api.weibo.com/oauth2/access_token'
    data = {
        'client_id': APP_KEY,
        'client_secret': APP_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    
    try:
        response = requests.post(token_url, data=data)
        response_json = response.json()
        logging.info(f"Token 响应: {response_json}")
        
        if response.status_code == 200 and 'access_token' in response_json:
            access_token = response_json['access_token']
            logging.info(f"获取到 access_token: {access_token}")
            auth_event.set()  # 设置事件状态为已授权
            return '授权成功！请返回控制台继续操作。'
        else:
            logging.error(f"获取 token 失败: {response.text}")
            return '授权失败！请检查控制台日志。'
    except Exception as e:
        logging.error(f"获取 token 时发生错误: {str(e)}")
        return '授权过程中发生错误！'

def get_pois_by_location(lat, lon, city_name, radius=3000):
    """获取指定位置周围的 POI"""
    if not access_token:
        logging.error("未获取到 access_token")
        return []
    
    url = 'https://api.weibo.com/2/place/nearby/pois.json'
    params = {
        'access_token': access_token,
        'lat': lat,
        'long': lon,
        'range': radius,
        'count': 50,
        'sort': 0,  # 按权重排序
        'offset': 0
    }
    
    all_pois = []
    max_retries = 3
    
    try:
        for offset in range(0, 150, 50):  # 获取多页数据
            params['offset'] = offset
            retries = 0
            while retries < max_retries:
                try:
                    response = requests.get(url, params=params)
                    response_json = response.json()
                    
                    if 'pois' in response_json:
                        pois = response_json['pois']
                        for poi in pois:
                            poi['city'] = city_name  # 添加城市信息
                        all_pois.extend(pois)
                        logging.info(f"成功获取 {city_name} 的 {len(pois)} 个 POI")
                        break
                    else:
                        logging.warning(f"获取 {city_name} POI 数据格式异常: {response_json}")
                        retries += 1
                except Exception as e:
                    logging.error(f"获取 {city_name} POI 数据出错: {str(e)}")
                    retries += 1
                    time.sleep(2)
            
            if len(pois) < 50:  # 如果返回的数据少于50条，说明没有更多数据了
                break
            time.sleep(1)  # 请求间隔
            
    except Exception as e:
        logging.error(f"获取 {city_name} POI 数据时发生错误: {str(e)}")
    
    return all_pois

def get_poi_comments(poi_id, poi_title):
    """获取 POI 的评论"""
    if not access_token:
        return []
    
    url = 'https://api.weibo.com/2/place/poi_timeline.json'
    params = {
        'access_token': access_token,
        'poiid': poi_id,
        'count': 50,
        'page': 1
    }
    
    all_comments = []
    max_retries = 3
    
    try:
        for page in range(1, 4):  # 获取前3页评论
            params['page'] = page
            retries = 0
            while retries < max_retries:
                try:
                    response = requests.get(url, params=params)
                    response_json = response.json()
                    
                    if 'statuses' in response_json:
                        comments = response_json['statuses']
                        logging.info(f"成功获取 POI: {poi_title} 的 {len(comments)} 条评论")
                        all_comments.extend(comments)
                        break
                    else:
                        logging.warning(f"获取 POI: {poi_title} 评论数据格式异常: {response_json}")
                        retries += 1
                except Exception as e:
                    logging.error(f"获取 POI: {poi_title} 评论数据出错: {str(e)}")
                    retries += 1
                    time.sleep(2)
            
            if len(comments) < 50:  # 如果返回的数据少于50条，说明没有更多数据了
                break
            time.sleep(1)  # 请求间隔
            
    except Exception as e:
        logging.error(f"获取 POI: {poi_title} 评论数据时发生错误: {str(e)}")
    
    return all_comments

def analyze_sentiment(text):
    """使用 SnowNLP 分析文本情感"""
    try:
        s = SnowNLP(text)
        return s.sentiments
    except:
        return 0.5

def save_to_database(pois_data, comments_data):
    """保存数据到数据库"""
    conn = sqlite3.connect('weibo_data.db')
    c = conn.cursor()
    
    # 保存 POI 数据
    for poi in pois_data:
        c.execute('''INSERT OR REPLACE INTO pois 
                     (id, title, address, city, latitude, longitude, checkin_num, created_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 (poi['id'], poi['title'], poi['address'], poi['city'],
                  poi['lat'], poi['lon'], poi.get('checkin_num', 0),
                  datetime.now()))
    
    # 保存评论数据
    for comment in comments_data:
        sentiment_score = analyze_sentiment(comment['text'])
        c.execute('''INSERT OR REPLACE INTO comments
                     (id, poi_id, content, created_at, sentiment_score)
                     VALUES (?, ?, ?, ?, ?)''',
                 (comment['id'], comment['poi_id'], comment['text'],
                  datetime.strptime(comment['created_at'], '%a %b %d %H:%M:%S +0800 %Y'),
                  sentiment_score))
    
    conn.commit()
    conn.close()

def export_to_csv():
    """导出数据为 CSV 格式"""
    conn = sqlite3.connect('weibo_data.db')
    
    # 导出 POI 数据
    pois_df = pd.read_sql_query('''
        SELECT p.*, 
               COUNT(c.id) as comment_count,
               AVG(c.sentiment_score) as avg_sentiment
        FROM pois p
        LEFT JOIN comments c ON p.id = c.poi_id
        GROUP BY p.id
    ''', conn)
    
    # 导出评论数据
    comments_df = pd.read_sql_query('''
        SELECT c.*, p.title as poi_title, p.city
        FROM comments c
        JOIN pois p ON c.poi_id = p.id
    ''', conn)
    
    conn.close()
    
    # 保存为 CSV 文件
    pois_df.to_csv('pois_data.csv', index=False, encoding='utf-8-sig')
    comments_df.to_csv('comments_data.csv', index=False, encoding='utf-8-sig')

def wait_for_token(timeout=300):  # 5分钟超时
    """等待获取访问令牌"""
    print("\n请在浏览器中完成微博授权...")
    print("等待授权中...", end="", flush=True)
    
    # 等待授权事件
    while not auth_event.wait(2):  # 每2秒检查一次
        if timeout <= 0:
            print("\n授权超时！请重新运行程序。")
            return False
        print(".", end="", flush=True)
        timeout -= 2
    
    print("\n授权成功！")
    return True

def main():
    """主函数"""
    logging.info("开始运行数据采集程序...")
    
    # 初始化数据库
    init_database()
    
    # 启动 Flask 服务器
    server = Thread(target=lambda: app.run(port=8080, debug=False))
    server.daemon = True  # 设置为守护线程，这样主程序退出时会自动结束
    server.start()
    time.sleep(1)  # 等待服务器启动
    logging.info("Flask 服务器已启动")
    
    # 打开浏览器进行授权
    print("正在打开浏览器进行微博授权...")
    webbrowser.open(OAUTH_URL)
    
    # 等待获取 access_token
    if not wait_for_token():
        return
    
    logging.info("授权成功！开始获取数据...")
    
    try:
        all_pois = []
        all_comments = []
        
        # 获取每个城市的 POI 数据
        for city, coords in SHANDONG_CITIES.items():
            logging.info(f"正在获取 {city} 的数据...")
            pois = get_pois_by_location(coords['lat'], coords['lon'], city)
            
            if not pois:
                logging.warning(f"{city} 未获取到 POI 数据")
                continue
                
            for poi in pois:
                logging.info(f"正在获取 POI: {poi.get('title', 'Unknown')} 的评论...")
                comments = get_poi_comments(poi.get('poiid'), poi.get('title', 'Unknown'))
                for comment in comments:
                    comment['poi_id'] = poi.get('poiid')
                    comment['poi_title'] = poi.get('title')
                    comment['city'] = city
                all_comments.extend(comments)
            
            all_pois.extend(pois)
            time.sleep(2)  # 避免请求过于频繁
        
        if not all_pois:
            logging.error("未获取到任何 POI 数据！")
            return
            
        # 保存数据到数据库
        logging.info(f"开始保存 {len(all_pois)} 个 POI 和 {len(all_comments)} 条评论...")
        save_to_database(all_pois, all_comments)
        
        # 导出数据为 CSV
        export_to_csv()
        logging.info("数据获取完成！数据已保存到 pois_data.csv 和 comments_data.csv")
        
    except KeyboardInterrupt:
        logging.info("程序被用户中断")
    except Exception as e:
        logging.error(f"程序执行出错: {str(e)}")
    finally:
        print("\n程序结束。如果需要重新运行，请直接执行 python dataload.py")

if __name__ == '__main__':
    main()
