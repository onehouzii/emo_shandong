import requests
import pandas as pd
import time
from typing import List, Dict

# 高德地图API配置
API_KEY = '2efd5a7585641fe216494c0111d5dd3b'  # emomap的API密钥
CITY = '370300'  # 淄博市的城市编码

# POI类型列表 (使用高德POI分类编码)
POI_TYPES = [
    {'type': '060100', 'name': '商场', 'weight': 0.7},  # 商场
    {'type': '141200', 'name': '学校', 'weight': 0.5},  # 学校
    {'type': '090100', 'name': '医院', 'weight': -0.3},  # 医院
    {'type': '110100', 'name': '公园', 'weight': 0.8},  # 公园
    {'type': '110200', 'name': '旅游景点', 'weight': 0.9},  # 旅游景点
    {'type': '050000', 'name': '餐饮', 'weight': 0.6},  # 餐饮
    {'type': '060100', 'name': '购物中心', 'weight': 0.7},  # 购物中心
    {'type': '140000', 'name': '文化场馆', 'weight': 0.6},  # 文化场馆
    {'type': '080100', 'name': '体育场馆', 'weight': 0.7},  # 体育场馆
]

def get_pois(poi_type: Dict, page: int = 1) -> List[Dict]:
    """
    获取指定类型的POI数据
    """
    url = 'https://restapi.amap.com/v3/place/text'
    params = {
        'key': API_KEY,
        'types': poi_type['type'],
        'city': CITY,
        'citylimit': 'true',  # 仅返回指定城市数据
        'offset': 20,  # 每页返回结果数
        'page': page,
        'extensions': 'base'
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        print(f"API响应: {data}")  # 打印API响应
        
        if data['status'] == '1':  # API调用成功
            if 'pois' in data and data['pois']:
                print(f"找到{len(data['pois'])}个{poi_type['name']}的POI数据")
                return data['pois']
            print(f"未找到{poi_type['name']}的POI数据")
        else:
            print(f"API调用失败: {data.get('info', '未知错误')}")
        return []
    except Exception as e:
        print(f"获取POI数据时出错: {e}")
        return []

def main():
    all_pois = []
    
    for poi_type in POI_TYPES:
        print(f"\n正在获取{poi_type['name']}的数据...")
        page = 1
        while True:
            pois = get_pois(poi_type, page)
            if not pois:
                break
                
            for poi in pois:
                location = poi['location'].split(',')
                all_pois.append({
                    '名称': poi['name'],
                    '类型': poi_type['name'],
                    '经度': location[0],
                    '纬度': location[1],
                    '情绪权重': poi_type['weight'],
                    '地址': poi.get('address', ''),
                    'POI编码': poi.get('id', '')
                })
            
            page += 1
            time.sleep(0.5)  # 添加延迟避免请求过快
    
    # 将数据保存为CSV
    if all_pois:
        df = pd.DataFrame(all_pois)
        df.to_csv('zibo_pois.csv', index=False, encoding='utf-8-sig')
        print(f"\n数据已保存到zibo_pois.csv，共收集{len(all_pois)}个地点信息")
    else:
        print("\n未能获取到任何POI数据")

if __name__ == '__main__':
    main() 