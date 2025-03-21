import requests
import pandas as pd
import json
from datetime import datetime
import time

class ZiboEmotionAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3"
        self.emotion_weights = {
            '商场': 0.7,
            '公园': 0.8,
            '医院': -0.3,
            '学校': 0.5,
            '景点': 0.9,
            '体育场所': 0.7,
            '文化场馆': 0.6,
            '餐饮': 0.6,
            '休闲娱乐': 0.7
        }
        
    def get_poi_data(self, poi_type, city="淄博"):
        """获取指定类型的POI数据"""
        pois = []
        page = 1
        while True:
            params = {
                'key': self.api_key,
                'city': city,
                'types': poi_type,
                'offset': 25,
                'page': page,
                'extensions': 'all'
            }
            
            try:
                response = requests.get(f"{self.base_url}/place/text", params=params)
                result = response.json()
                
                if result['status'] == '1':  # 请求成功
                    if not result['pois']:  # 没有更多数据
                        break
                    
                    pois.extend(result['pois'])
                    page += 1
                    time.sleep(0.5)  # 避免请求过于频繁
                else:
                    print(f"请求失败: {result}")
                    break
                    
            except Exception as e:
                print(f"获取POI数据时出错: {e}")
                break
                
        return pois

    def get_weather_data(self, city="淄博"):
        """获取天气数据"""
        params = {
            'key': self.api_key,
            'city': city,
            'extensions': 'base'
        }
        
        try:
            response = requests.get(f"{self.base_url}/weather/weatherInfo", params=params)
            result = response.json()
            if result['status'] == '1':
                return result['lives'][0]
        except Exception as e:
            print(f"获取天气数据时出错: {e}")
        
        return None

    def calculate_emotion_score(self, poi_type, time_period, weather_data):
        """计算情绪得分"""
        base_score = self.emotion_weights.get(poi_type, 0)
        
        # 时间权重
        time_weights = {
            'morning': 0.6,
            'noon': 0.4,
            'afternoon': 0.7,
            'evening': 0.8
        }
        time_weight = time_weights.get(time_period, 0.5)
        
        # 天气权重
        weather_weights = {
            '晴': 0.8,
            '多云': 0.6,
            '阴': 0.4,
            '雨': 0.3
        }
        weather_weight = weather_weights.get(weather_data.get('weather', '晴'), 0.5)
        
        # 综合计算
        emotion_score = base_score * 0.5 + time_weight * 0.3 + weather_weight * 0.2
        return round(emotion_score, 2)

    def analyze_city_emotion(self):
        """分析城市情绪"""
        # 获取当前时间段
        hour = datetime.now().hour
        if 6 <= hour < 11:
            time_period = 'morning'
        elif 11 <= hour < 14:
            time_period = 'noon'
        elif 14 <= hour < 18:
            time_period = 'afternoon'
        else:
            time_period = 'evening'

        # 获取天气数据
        weather_data = self.get_weather_data()
        
        all_pois = []
        # 获取各类型POI数据
        for poi_type in self.emotion_weights.keys():
            pois = self.get_poi_data(poi_type)
            for poi in pois:
                emotion_score = self.calculate_emotion_score(poi_type, time_period, weather_data)
                poi_data = {
                    '名称': poi['name'],
                    '类型': poi_type,
                    '经度': poi['location'].split(',')[0],
                    '纬度': poi['location'].split(',')[1],
                    '地址': poi['address'],
                    '情绪权重': emotion_score,
                    '时间段': time_period,
                    '天气': weather_data['weather'] if weather_data else '',
                    '温度': weather_data['temperature'] if weather_data else ''
                }
                all_pois.append(poi_data)

        # 保存为CSV文件
        df = pd.DataFrame(all_pois)
        df.to_csv('zibo_emotion_pois.csv', index=False, encoding='utf-8')
        print(f"共获取 {len(all_pois)} 个POI数据点")
        
        return all_pois

if __name__ == "__main__":
    API_KEY = "2efd5a7585641fe216494c0111d5dd3b"  # 替换为您的高德API密钥
    analyzer = ZiboEmotionAnalyzer(API_KEY)
    analyzer.analyze_city_emotion() 