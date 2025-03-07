from shapely.geometry import Polygon, Point
import numpy as np
import pandas as pd
import random

# 山东省近似多边形坐标（优化版20顶点）
shandong_coords = [
    (115.500000, 35.200000), (116.300000, 36.000000),
    (117.000000, 36.600000), (118.300000, 37.400000),
    (119.100000, 37.400000), (120.300000, 37.500000),
    (121.500000, 37.500000), (122.400000, 37.000000),
    (122.700000, 36.000000), (121.500000, 35.500000),
    (120.300000, 34.800000), (118.800000, 34.800000),
    (117.200000, 34.200000), (116.000000, 34.400000),
    (115.500000, 35.200000), (116.800000, 36.800000),
    (117.800000, 37.200000), (118.500000, 37.300000),
    (119.800000, 37.400000), (115.500000, 35.200000)  # 闭合
]

polygon = Polygon(shandong_coords)

# 人口密度权重配置（城市中心+标准差）
population_centers = [
    # (经度, 纬度, 生成权重, 分布标准差)
    (117.0000, 36.6500, 0.18, 0.4),  # 济南
    (120.3833, 36.0667, 0.22, 0.5),  # 青岛
    (118.0500, 36.7833, 0.12, 0.3),  # 淄博
    (119.1000, 37.4000, 0.08, 0.6),  # 东营
    (121.3914, 37.5393, 0.10, 0.4),  # 烟台
    (122.1167, 37.5000, 0.07, 0.3),  # 威海
    (118.3500, 35.0500, 0.15, 0.5),  # 临沂
    (116.5867, 35.4150, 0.08, 0.4),  # 济宁
]

# 权重标准化
weights = np.array([c[2] for c in population_centers])
probabilities = weights / weights.sum()

data = []
while len(data) < 1000:
    # 按人口密度选择生成中心
    center = population_centers[np.random.choice(len(population_centers), p=probabilities)]
    
    # 生成正态分布坐标
    lon = np.random.normal(center[0], center[3]/2)  # 标准差减半防止过度扩散
    lat = np.random.normal(center[1], center[3]/2)
    
    # 严格边界检查
    if polygon.contains(Point(lon, lat)):
        data.append([
            round(lon, 6),  # 经度保留6位小数
            round(lat, 6),  # 纬度保留6位小数
            random.randint(1, 7)  # 情绪值单列
        ])

# 创建DataFrame并保存
df = pd.DataFrame(data, columns=['lon', 'lat', 'emo'])
df.to_csv('shandong_emotion_data.csv', index=False, float_format='%.6f')
print(f"成功生成{len(data)}条数据，示例：\n{df.head()}")