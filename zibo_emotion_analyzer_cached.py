import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os
import pickle
from pathlib import Path

class ZiboEmotionAnalyzerCached:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3"
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # 载入缓存的POI数据
        self.poi_cache_file = self.cache_dir / "poi_cache.pkl"
        self.weather_cache_file = self.cache_dir / "weather_cache.pkl"
        self.poi_cache = self._load_cache(self.poi_cache_file)
        self.weather_cache = self._load_cache(self.weather_cache_file)
        
        # POI类型权重配置
        self.poi_weights = {
            '商场': {
                'base_weight': 0.7,
                'crowd_sensitivity': 0.8,
                'time_sensitivity': 0.7,
                'weather_sensitivity': 0.5
            },
            '公园': {
                'base_weight': 0.8,
                'crowd_sensitivity': 0.6,
                'time_sensitivity': 0.8,
                'weather_sensitivity': 0.9
            },
            '医院': {
                'base_weight': -0.3,
                'crowd_sensitivity': 0.9,
                'time_sensitivity': 0.5,
                'weather_sensitivity': 0.3
            },
            '学校': {
                'base_weight': 0.5,
                'crowd_sensitivity': 0.8,
                'time_sensitivity': 0.9,
                'weather_sensitivity': 0.6
            },
            '景点': {
                'base_weight': 0.9,
                'crowd_sensitivity': 0.7,
                'time_sensitivity': 0.8,
                'weather_sensitivity': 0.9
            }
        }
        
        # 时间权重配置
        self.time_weights = {
            'weekday': {
                'morning': {'weight': 0.6, 'peak_hours': [8, 9]},
                'noon': {'weight': 0.4, 'peak_hours': [12, 13]},
                'afternoon': {'weight': 0.7, 'peak_hours': [14, 15, 16]},
                'evening': {'weight': 0.8, 'peak_hours': [18, 19, 20]}
            },
            'weekend': {
                'morning': {'weight': 0.7, 'peak_hours': [9, 10, 11]},
                'noon': {'weight': 0.6, 'peak_hours': [12, 13]},
                'afternoon': {'weight': 0.8, 'peak_hours': [15, 16, 17]},
                'evening': {'weight': 0.9, 'peak_hours': [19, 20, 21]}
            }
        }
        
        # 天气影响因子
        self.weather_factors = {
            '晴': {
                'weight': 0.8,
                'humidity_factor': 0.7,
                'temperature_comfort': lambda t: 1 - abs(t - 23) / 20
            },
            '多云': {
                'weight': 0.6,
                'humidity_factor': 0.6,
                'temperature_comfort': lambda t: 1 - abs(t - 23) / 20
            },
            '阴': {
                'weight': 0.4,
                'humidity_factor': 0.5,
                'temperature_comfort': lambda t: 1 - abs(t - 23) / 20
            },
            '雨': {
                'weight': 0.3,
                'humidity_factor': 0.3,
                'temperature_comfort': lambda t: 1 - abs(t - 23) / 20
            }
        }

    def _load_cache(self, cache_file):
        """加载缓存数据"""
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"加载缓存文件 {cache_file} 时出错: {e}")
        return {}

    def _save_cache(self, cache_data, cache_file):
        """保存缓存数据"""
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
        except Exception as e:
            print(f"保存缓存文件 {cache_file} 时出错: {e}")

    def get_poi_data(self, poi_type, city="淄博", force_update=False):
        """获取POI数据（带缓存）"""
        cache_key = f"{city}_{poi_type}"
        
        # 如果不强制更新且缓存中有数据，直接返回缓存数据
        if not force_update and cache_key in self.poi_cache:
            print(f"使用缓存的{poi_type}数据")
            return self.poi_cache[cache_key]
        
        print(f"从API获取{poi_type}数据")
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
                
                if result['status'] == '1':
                    if not result['pois']:
                        break
                    
                    pois.extend(result['pois'])
                    page += 1
                    time.sleep(0.5)
                else:
                    print(f"请求失败: {result}")
                    break
                    
            except Exception as e:
                print(f"获取POI数据时出错: {e}")
                break
        
        if pois:  # 只在成功获取数据时更新缓存
            self.poi_cache[cache_key] = pois
            self._save_cache(self.poi_cache, self.poi_cache_file)
            
        return pois

    def get_weather_data(self, city="淄博", force_update=False):
        """获取天气数据（带缓存）"""
        cache_key = f"{city}_{datetime.now().strftime('%Y-%m-%d')}"
        
        # 如果不强制更新且缓存中有当天的数据，直接返回缓存数据
        if not force_update and cache_key in self.weather_cache:
            print("使用缓存的天气数据")
            return self.weather_cache[cache_key]
            
        print("从API获取天气数据")
        params = {
            'key': self.api_key,
            'city': city,
            'extensions': 'all'
        }
        
        try:
            response = requests.get(f"{self.base_url}/weather/weatherInfo", params=params)
            result = response.json()
            
            if result['status'] == '1':
                weather_data = {
                    'current': result['lives'][0] if 'lives' in result else None,
                    'forecast': result['forecasts'][0]['casts'] if 'forecasts' in result else None
                }
                
                # 更新缓存
                self.weather_cache[cache_key] = weather_data
                self._save_cache(self.weather_cache, self.weather_cache_file)
                
                return weather_data
                
        except Exception as e:
            print(f"获取天气数据时出错: {e}")
            
        return None

    def estimate_crowd_density(self, poi, time_period, is_weekend):
        """估算人群密度"""
        base_capacity = {
            '商场': 2000,
            '公园': 1500,
            '医院': 1000,
            '学校': 3000,
            '景点': 2000
        }
        
        capacity = base_capacity.get(poi['type'], 1000)
        time_factor = self.time_weights['weekend' if is_weekend else 'weekday'][time_period]['weight']
        location_factor = float(poi.get('biz_ext', {}).get('rating', '0')) / 5.0 if poi.get('biz_ext', {}).get('rating') else 0.5
        
        return capacity * time_factor * location_factor

    def calculate_emotion_score(self, poi, time_period, weather_data, is_weekend):
        """计算情绪得分"""
        poi_type = poi['type']
        poi_info = self.poi_weights[poi_type]
        
        # 基础得分
        base_score = poi_info['base_weight']
        
        # 人群密度影响
        crowd_density = self.estimate_crowd_density(poi, time_period, is_weekend)
        crowd_factor = 1 - (crowd_density / 10000)
        crowd_score = crowd_factor * poi_info['crowd_sensitivity']
        
        # 时间影响
        time_weight = self.time_weights['weekend' if is_weekend else 'weekday'][time_period]['weight']
        time_score = time_weight * poi_info['time_sensitivity']
        
        # 天气影响
        if weather_data and 'weather' in weather_data:
            weather = weather_data['weather']
            temperature = float(weather_data.get('temperature', 23))
            weather_info = self.weather_factors[weather]
            weather_score = (weather_info['weight'] * 
                           weather_info['temperature_comfort'](temperature) * 
                           poi_info['weather_sensitivity'])
        else:
            weather_score = 0.5 * poi_info['weather_sensitivity']
        
        # 综合计算
        emotion_score = (base_score * 0.4 + 
                        crowd_score * 0.2 + 
                        time_score * 0.2 + 
                        weather_score * 0.2)
        
        return round(emotion_score, 2)

    def analyze_city_emotion(self, force_update=False):
        """分析城市情绪"""
        try:
            # 获取当前时间信息
            current_time = datetime.now()
            is_weekend = current_time.weekday() >= 5
            
            hour = current_time.hour
            if 6 <= hour < 11:
                time_period = 'morning'
            elif 11 <= hour < 14:
                time_period = 'noon'
            elif 14 <= hour < 18:
                time_period = 'afternoon'
            else:
                time_period = 'evening'

            # 获取天气数据
            weather_data = self.get_weather_data(force_update=force_update)
            current_weather = weather_data['current'] if weather_data else None
            
            all_pois = []
            
            # 获取各类型POI数据
            for poi_type in self.poi_weights.keys():
                try:
                    pois = self.get_poi_data(poi_type, force_update=force_update)
                    if not pois:
                        print(f"警告：无法获取{poi_type}的POI数据")
                        continue
                        
                    for poi in pois:
                        # 添加类型信息
                        poi['type'] = poi_type
                        
                        # 计算人群密度
                        crowd_density = self.estimate_crowd_density(poi, time_period, is_weekend)
                        
                        # 计算情绪得分
                        emotion_score = self.calculate_emotion_score(poi, time_period, current_weather, is_weekend)
                        
                        # 准备POI数据
                        poi_data = {
                            '名称': poi['name'],
                            '类型': poi_type,
                            '经度': poi['location'].split(',')[0],
                            '纬度': poi['location'].split(',')[1],
                            '地址': poi['address'],
                            '情绪权重': emotion_score,
                            '时间段': time_period,
                            '天气': current_weather['weather'] if current_weather else '',
                            '温度': current_weather['temperature'] if current_weather else '',
                            '人群密度': crowd_density,
                            '是否周末': is_weekend
                        }
                        all_pois.append(poi_data)
                        
                except Exception as e:
                    print(f"处理{poi_type}数据时出错: {e}")
                    continue

            if not all_pois:
                print("警告：未能获取任何POI数据")
                return None

            # 转换为DataFrame并保存
            df = pd.DataFrame(all_pois)
            df.to_csv('zibo_emotion_pois.csv', index=False, encoding='utf-8')
            
            print(f"共分析 {len(all_pois)} 个POI数据点")
            print(f"数据已保存到 zibo_emotion_pois.csv")
            
            return {
                'current_data': all_pois,
                'time_period': time_period,
                'weather': current_weather
            }
            
        except Exception as e:
            print(f"分析过程出错: {e}")
            return None

class ZiboAlternativeEmotionAnalyzer:
    def __init__(self):
        self.time_patterns = {
            'weekday': {
                'morning': {'crowd_factor': 0.8, 'hours': [7, 8, 9], 'emotion_base': 0.6},
                'noon': {'crowd_factor': 0.6, 'hours': [11, 12, 13], 'emotion_base': 0.5},
                'afternoon': {'crowd_factor': 0.7, 'hours': [14, 15, 16], 'emotion_base': 0.7},
                'evening': {'crowd_factor': 0.9, 'hours': [17, 18, 19], 'emotion_base': 0.8}
            },
            'weekend': {
                'morning': {'crowd_factor': 0.6, 'hours': [9, 10, 11], 'emotion_base': 0.7},
                'noon': {'crowd_factor': 0.8, 'hours': [12, 13, 14], 'emotion_base': 0.8},
                'afternoon': {'crowd_factor': 0.9, 'hours': [15, 16, 17], 'emotion_base': 0.8},
                'evening': {'crowd_factor': 0.9, 'hours': [18, 19, 20], 'emotion_base': 0.9}
            }
        }
        
        self.location_weights = {
            '商业区': {'base_score': 0.7, 'time_sensitivity': 0.8},
            '居住区': {'base_score': 0.6, 'time_sensitivity': 0.6},
            '教育区': {'base_score': 0.5, 'time_sensitivity': 0.9},
            '休闲区': {'base_score': 0.8, 'time_sensitivity': 0.7},
            '工业区': {'base_score': 0.4, 'time_sensitivity': 0.5}
        }
        
        self.weather_impact = {
            '晴': {'activity_factor': 0.9, 'emotion_factor': 0.8},
            '多云': {'activity_factor': 0.8, 'emotion_factor': 0.7},
            '阴': {'activity_factor': 0.6, 'emotion_factor': 0.5},
            '雨': {'activity_factor': 0.4, 'emotion_factor': 0.4},
            '雪': {'activity_factor': 0.5, 'emotion_factor': 0.6}
        }

    def get_time_based_emotion(self, hour, is_weekend):
        """基于时间估算情绪值"""
        day_type = 'weekend' if is_weekend else 'weekday'
        
        for period, data in self.time_patterns[day_type].items():
            if hour in data['hours']:
                return {
                    'period': period,
                    'crowd_factor': data['crowd_factor'],
                    'emotion_base': data['emotion_base']
                }
        
        return {
            'period': 'other',
            'crowd_factor': 0.5,
            'emotion_base': 0.5
        }

    def get_weather_based_activity(self, weather):
        """基于天气估算活动倾向"""
        return self.weather_impact.get(weather, {
            'activity_factor': 0.6,
            'emotion_factor': 0.5
        })

    def analyze_alternative_emotion(self, weather_data=None):
        """使用替代数据源分析城市情绪"""
        current_time = datetime.now()
        is_weekend = current_time.weekday() >= 5
        hour = current_time.hour
        
        # 获取时间基础情绪值
        time_emotion = self.get_time_based_emotion(hour, is_weekend)
        
        # 获取天气影响
        weather = '晴'  # 默认值
        if weather_data and 'weather' in weather_data:
            weather = weather_data['weather']
        weather_factors = self.get_weather_based_activity(weather)
        
        # 计算综合情绪值
        areas_emotion = []
        for area, weights in self.location_weights.items():
            emotion_score = (
                weights['base_score'] * 0.3 +
                time_emotion['emotion_base'] * weights['time_sensitivity'] * 0.3 +
                weather_factors['emotion_factor'] * 0.2 +
                time_emotion['crowd_factor'] * 0.2
            )
            
            areas_emotion.append({
                '区域': area,
                '时间段': time_emotion['period'],
                '天气': weather,
                '情绪值': round(emotion_score, 2),
                '人流量预估': round(time_emotion['crowd_factor'] * weather_factors['activity_factor'], 2),
                '时间': current_time.strftime('%Y-%m-%d %H:%M')
            })
        
        # 保存结果
        df = pd.DataFrame(areas_emotion)
        df.to_csv('zibo_alternative_emotion.csv', index=False, encoding='utf-8')
        
        return {
            'areas_emotion': areas_emotion,
            'time_period': time_emotion['period'],
            'weather': weather
        }

if __name__ == "__main__":
    API_KEY = "2efd5a7585641fe216494c0111d5dd3b"
    analyzer = ZiboEmotionAnalyzerCached(API_KEY)
    
    # 首次运行使用force_update=True强制从API获取数据
    # 后续运行可以设置force_update=False使用缓存数据
    results = analyzer.analyze_city_emotion(force_update=True)
    
    # 使用替代分析器
    alternative_analyzer = ZiboAlternativeEmotionAnalyzer()
    alternative_results = alternative_analyzer.analyze_alternative_emotion()
    print("替代数据分析完成，结果已保存到 zibo_alternative_emotion.csv") 