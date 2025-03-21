import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
import joblib
import warnings
warnings.filterwarnings('ignore')

class ZiboEmotionAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3"
        
        # POI类型权重（基于心理学研究和城市规划理论）
        self.poi_weights = {
            '商场': {
                'base_weight': 0.7,
                'crowd_sensitivity': 0.8,  # 人群密度敏感度
                'time_sensitivity': 0.7,   # 时间敏感度
                'weather_sensitivity': 0.5  # 天气敏感度
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
            },
            '体育场所': {
                'base_weight': 0.7,
                'crowd_sensitivity': 0.7,
                'time_sensitivity': 0.8,
                'weather_sensitivity': 0.8
            },
            '文化场馆': {
                'base_weight': 0.6,
                'crowd_sensitivity': 0.6,
                'time_sensitivity': 0.7,
                'weather_sensitivity': 0.5
            },
            '餐饮': {
                'base_weight': 0.6,
                'crowd_sensitivity': 0.9,
                'time_sensitivity': 0.9,
                'weather_sensitivity': 0.4
            }
        }
        
        # 时间权重（基于生理节律和社会活动规律）
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
        
        # 天气影响因子（基于环境心理学研究）
        self.weather_factors = {
            '晴': {
                'weight': 0.8,
                'humidity_factor': 0.7,
                'temperature_comfort': lambda t: 1 - abs(t - 23) / 20  # 最适温度23度
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
        
        # 初始化机器学习模型
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = MinMaxScaler()
        
    def get_poi_data(self, poi_type, city="淄博"):
        """获取POI数据并计算人口密度估计"""
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
                
        return pois

    def estimate_crowd_density(self, poi, time_period, is_weekend):
        """估算人群密度"""
        base_capacity = {
            '商场': 2000,
            '公园': 1500,
            '医院': 1000,
            '学校': 3000,
            '景点': 2000,
            '体育场所': 1000,
            '文化场馆': 800,
            '餐饮': 200
        }
        
        # 获取基础容量
        capacity = base_capacity.get(poi['type'], 1000)
        
        # 时间影响因子
        time_factor = self.time_weights['weekend' if is_weekend else 'weekday'][time_period]['weight']
        
        # 位置影响因子（基于POI评分）
        location_factor = float(poi.get('biz_ext', {}).get('rating', '0')) / 5.0 if poi.get('biz_ext', {}).get('rating') else 0.5
        
        # 估算当前人数
        estimated_crowd = capacity * time_factor * location_factor
        
        return estimated_crowd

    def get_weather_data(self, city="淄博"):
        """获取天气数据"""
        params = {
            'key': self.api_key,
            'city': city,
            'extensions': 'all'  # 获取预报数据
        }
        
        try:
            response = requests.get(f"{self.base_url}/weather/weatherInfo", params=params)
            result = response.json()
            if result['status'] == '1':
                return {
                    'current': result['lives'][0] if 'lives' in result else None,
                    'forecast': result['forecasts'][0]['casts'] if 'forecasts' in result else None
                }
        except Exception as e:
            print(f"获取天气数据时出错: {e}")
        
        return None

    def calculate_emotion_score(self, poi, time_period, weather_data, is_weekend):
        """计算综合情绪得分"""
        poi_type = poi['type']
        poi_info = self.poi_weights[poi_type]
        
        # 基础得分
        base_score = poi_info['base_weight']
        
        # 人群密度影响
        crowd_density = self.estimate_crowd_density(poi, time_period, is_weekend)
        crowd_factor = 1 - (crowd_density / 10000)  # 归一化
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

    def predict_future_emotion(self, historical_data, future_days=7):
        """预测未来情绪趋势"""
        if len(historical_data) == 0:
            print("警告：没有足够的历史数据进行预测")
            return []
        
        # 准备特征
        features = ['人群密度', '时间权重', '天气得分', '是否周末']
        if not all(f in historical_data.columns for f in features):
            # 如果数据结构不匹配，重命名列
            historical_data = historical_data.rename(columns={
                'crowd_density': '人群密度',
                'time_weight': '时间权重',
                'weather_score': '天气得分',
                'is_weekend': '是否周末'
            })
        
        try:
            X = historical_data[features]
            y = historical_data['情绪权重']
            
            # 训练模型
            self.model.fit(X, y)
            
            # 生成未来日期的预测数据
            future_predictions = []
            current_date = datetime.now()
            
            for i in range(future_days):
                future_date = current_date + timedelta(days=i)
                is_weekend = future_date.weekday() >= 5
                
                # 为每个时间段生成预测
                for period in ['morning', 'noon', 'afternoon', 'evening']:
                    prediction = {
                        'date': future_date.strftime('%Y-%m-%d'),
                        'time_period': period,
                        'predicted_emotion': None,
                        'confidence': None
                    }
                    
                    # 获取预测所需特征
                    features = np.array([[
                        0.5,  # 平均人群密度
                        self.time_weights['weekend' if is_weekend else 'weekday'][period]['weight'],
                        0.6,  # 平均天气得分
                        int(is_weekend)
                    ]])
                    
                    # 预测情绪得分
                    try:
                        predicted_score = self.model.predict(features)[0]
                        prediction['predicted_emotion'] = round(predicted_score, 2)
                        prediction['confidence'] = 0.5  # 简化置信度计算
                    except Exception as e:
                        print(f"预测出错: {e}")
                        prediction['predicted_emotion'] = 0
                        prediction['confidence'] = 0
                    
                    future_predictions.append(prediction)
            
            return future_predictions
        except Exception as e:
            print(f"预测过程出错: {e}")
            return []

    def generate_emotion_warning(self, emotion_data, threshold=0.8):
        """生成情绪预警"""
        warnings = []
        
        # 按区域聚合情绪数据
        grouped_data = pd.DataFrame(emotion_data).groupby('区域')
        
        for area, data in grouped_data:
            avg_emotion = data['emotion_score'].mean()
            crowd_density = data['crowd_density'].mean()
            
            # 检查高负面情绪
            if avg_emotion < -threshold:
                warnings.append({
                    '区域': area,
                    '类型': '负面情绪预警',
                    '等级': 'high',
                    '描述': f'区域{area}出现明显负面情绪趋势，建议关注'
                })
            
            # 检查人群密度异常
            if crowd_density > threshold * 10000:
                warnings.append({
                    '区域': area,
                    '类型': '人群密度预警',
                    '等级': 'medium',
                    '描述': f'区域{area}人群密度较高，建议疏导'
                })
        
        return warnings

    def analyze_city_emotion(self):
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
            weather_data = self.get_weather_data()
            current_weather = weather_data['current'] if weather_data else None
            
            all_pois = []
            historical_data = []
            
            # 获取各类型POI数据
            for poi_type in self.poi_weights.keys():
                try:
                    pois = self.get_poi_data(poi_type)
                    if not pois:  # 如果API限制，跳过继续处理已有数据
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
                        
                        # 准备历史数据用于预测
                        historical_data.append({
                            '人群密度': crowd_density,
                            '时间权重': self.time_weights['weekend' if is_weekend else 'weekday'][time_period]['weight'],
                            '天气得分': self.weather_factors[current_weather['weather']]['weight'] if current_weather else 0.5,
                            '是否周末': int(is_weekend),
                            '情绪权重': emotion_score
                        })
                except Exception as e:
                    print(f"处理{poi_type}数据时出错: {e}")
                    continue

            if not all_pois:
                print("警告：未能获取任何POI数据")
                return None

            # 转换为DataFrame
            df = pd.DataFrame(all_pois)
            df_historical = pd.DataFrame(historical_data)
            
            # 保存当前数据
            df.to_csv('zibo_emotion_pois.csv', index=False, encoding='utf-8')
            
            # 生成预测
            future_predictions = self.predict_future_emotion(df_historical)
            
            # 生成预警
            warnings = self.generate_emotion_warning(all_pois)
            
            # 保存预测结果
            if future_predictions:
                pd.DataFrame(future_predictions).to_csv('zibo_emotion_predictions.csv', index=False, encoding='utf-8')
            
            # 保存预警信息
            if warnings:
                pd.DataFrame(warnings).to_csv('zibo_emotion_warnings.csv', index=False, encoding='utf-8')
            
            print(f"共获取 {len(all_pois)} 个POI数据点")
            print(f"生成 {len(future_predictions)} 个预测数据点")
            print(f"发现 {len(warnings)} 个预警信息")
            
            return {
                'current_data': all_pois,
                'predictions': future_predictions,
                'warnings': warnings
            }
        except Exception as e:
            print(f"分析过程出错: {e}")
            return None

if __name__ == "__main__":
    API_KEY = "2efd5a7585641fe216494c0111d5dd3b"
    analyzer = ZiboEmotionAnalyzer(API_KEY)
    results = analyzer.analyze_city_emotion() 