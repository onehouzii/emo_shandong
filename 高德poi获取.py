import requests
import pandas as pd
import time
from collections import defaultdict

def get_pois(city, types, api_key):
    """获取指定城市和类型的POI数据"""
    base_url = "https://restapi.amap.com/v3/place/text"
    all_pois = []
    
    for type_name in types:
        page = 1
        while True:
            params = {
                'key': api_key,
                'keywords': '',  # 关键词留空，按类型搜索
                'types': type_name,
                'city': city,
                'citylimit': 'true',  # 仅搜索指定城市
                'output': 'json',
                'offset': 25,  # 每页记录数
                'page': page,
                'extensions': 'all'  # 返回详细信息
            }
            
            try:
                response = requests.get(base_url, params=params)
                result = response.json()
                
                if result['status'] == '0':
                    print(f"请求失败: {result}")
                    break
                
                pois = result['pois']
                if not pois:  # 如果没有更多数据，退出循环
                    break
                
                # 处理每个POI
                for poi in pois:
                    # 提取区域信息
                    district = poi.get('adname', '').replace('区', '')
                    if not district or district == city:
                        district = poi.get('business', '未知区域')
                    
                    # 添加到结果列表
                    all_pois.append({
                        '地点名称': poi['name'],
                        '类型': type_name,
                        '经度': float(poi['location'].split(',')[0]),
                        '纬度': float(poi['location'].split(',')[1]),
                        '情绪权重': 0.7,  # 默认情绪权重
                        '地址': poi['address'],
                        'POI编码': poi['id'],
                        '区域': district
                    })
                
                print(f"已获取 {type_name} 类型第 {page} 页数据，共 {len(pois)} 条")
                page += 1
                time.sleep(0.1)  # 添加延迟，避免请求过快
                
            except Exception as e:
                print(f"获取 {type_name} 数据时出错: {str(e)}")
                break
    
    return all_pois

def main():
    # 高德地图API密钥
    api_key = '2efd5a7585641fe216494c0111d5dd3b'
    
    # 要搜索的城市
    city = '淄博市'
    
    # 要搜索的POI类型
    poi_types = {
        '购物': '购物服务',
        '餐饮': '餐饮服务',
        '景点': '风景名胜',
        '教育': '科教文化服务',
        '医疗': '医疗保健服务',
        '文化': '文化场馆',
        '运动': '体育休闲服务',
        '休闲': '休闲场所'
    }
    
    # 获取所有POI数据
    all_pois = []
    for display_name, type_code in poi_types.items():
        print(f"\n开始获取{display_name}类型的POI...")
        pois = get_pois(city, type_code, api_key)
        
        # 更新POI类型显示名称
        for poi in pois:
            poi['类型'] = display_name
        
        all_pois.extend(pois)
        print(f"已获取{len(pois)}个{display_name}类型的POI")
    
    # 统计每个类型的POI数量
    type_counts = defaultdict(int)
    for poi in all_pois:
        type_counts[poi['类型']] += 1
    
    print("\nPOI类型统计：")
    for type_name, count in type_counts.items():
        print(f"{type_name}: {count}个")
    
    # 保存为CSV文件
    df = pd.DataFrame(all_pois)
    df.to_csv('zibo_pois_original.csv', index=False, encoding='utf-8-sig')
    print(f"\n数据已保存到 zibo_pois_original.csv，共 {len(all_pois)} 条记录")

if __name__ == "__main__":
    main() 