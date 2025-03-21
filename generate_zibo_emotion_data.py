import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

class ZiboLocationDataGenerator:
    def __init__(self):
        # 读取POI数据
        self.poi_df = pd.read_csv('淄博poi初始.csv')
        # 获取所有不同的地点名称及其信息
        self.unique_locations = []
        for _, group in self.poi_df.groupby('地点名称'):
            # 取每个地点的第一条记录作为基础信息
            location_info = group.iloc[0].to_dict()
            location_info['区域'] = '其他'  # 使用"其他"作为默认区域
            self.unique_locations.append(location_info)
        print(f"成功读取 {len(self.unique_locations)} 个不同地点")
        
        # 时间段设置
        self.time_periods = ['凌晨', '上午', '中午', '下午', '傍晚', '晚上', '深夜']
        
        # 节假日设置
        self.holidays = {
            '元旦': ['2024-01-01'],
            '春节': ['2024-02-10', '2024-02-11', '2024-02-12', '2024-02-13', '2024-02-14', '2024-02-15'],
            '清明节': ['2024-04-04', '2024-04-05', '2024-04-06'],
            '劳动节': ['2024-05-01', '2024-05-02', '2024-05-03', '2024-05-04', '2024-05-05'],
            '端午节': ['2024-06-10'],
            '中秋节': ['2024-09-17'],
            '国庆节': ['2024-10-01', '2024-10-02', '2024-10-03', '2024-10-04', '2024-10-05']
        }

    def get_daily_locations(self, date):
        # 每天随机选择50-80个不同的地点
        n_locations = random.randint(50, 80)
        selected_locations = random.sample(self.unique_locations, n_locations)
        
        # 为每个位置随机选择1-2个时间段
        final_locations = []
        for location in selected_locations:
            # 随机选择1-2个时间段
            n_periods = random.randint(1, 2)
            periods = random.sample(self.time_periods, n_periods)
            
            for period in periods:
                final_locations.append({
                    '日期': date,
                    '地点名称': location['地点名称'],
                    '经度': location['经度'],
                    '纬度': location['纬度'],
                    '区域': location['区域'],
                    '类型': location['类型'],
                    '时间段': period
                })
        
        return pd.DataFrame(final_locations)

    def calculate_emotion_value(self, row):
        base_score = 5.5  # 基础情绪值改为中间值5.5
        
        # 节假日影响
        date_str = row['日期']
        is_holiday = any(date_str in dates for dates in self.holidays.values())
        holiday_effect = random.uniform(0.5, 1.5) if is_holiday else 0
        
        # 周末影响
        date = datetime.strptime(date_str, '%Y-%m-%d')
        is_weekend = date.weekday() >= 5
        weekend_effect = random.uniform(0.3, 0.8) if is_weekend else 0
        
        # 时间段影响
        time_effects = {
            '凌晨': -1.5,
            '上午': 0.5,
            '中午': 0,
            '下午': 0.5,
            '傍晚': 0.3,
            '晚上': -0.5,
            '深夜': -1.0
        }
        time_effect = time_effects[row['时间段']]
        
        # 天气影响（模拟）
        weather_effect = random.uniform(-1.0, 1.0)
        
        # 随机波动
        random_effect = random.uniform(-1.5, 1.5)
        
        # 计算最终情绪值
        emotion_value = base_score + holiday_effect + weekend_effect + time_effect + weather_effect + random_effect
        
        # 确保情绪值在合理范围内
        return round(min(max(emotion_value, 1), 10), 2)

    def generate_monthly_data(self, year, month):
        # 获取月份的第一天和最后一天
        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # 生成该月每一天的数据
        all_data = []
        current_day = first_day
        while current_day <= last_day:
            date_str = current_day.strftime('%Y-%m-%d')
            daily_locations = self.get_daily_locations(date_str)
            
            # 计算情绪值
            daily_locations['情绪值'] = daily_locations.apply(self.calculate_emotion_value, axis=1)
            
            all_data.append(daily_locations)
            current_day += timedelta(days=1)
        
        # 合并所有数据
        monthly_data = pd.concat(all_data, ignore_index=True)
        return monthly_data

    def generate_year_data(self, year):
        total_records = 0
        for month in range(1, 13):
            monthly_data = self.generate_monthly_data(year, month)
            
            # 保存月度数据
            filename = f'emotion_data_{year}{month:02d}.csv'
            monthly_data.to_csv(filename, index=False, encoding='utf-8-sig')
            
            total_records += len(monthly_data)
            print(f"已生成 {year}年{month}月 的情绪数据，共 {len(monthly_data)} 条记录")
        
        print(f"\n全年共生成 {total_records} 条情绪数据记录")

# 运行数据生成
generator = ZiboLocationDataGenerator()
generator.generate_year_data(2024)