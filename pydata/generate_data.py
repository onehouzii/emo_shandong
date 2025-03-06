import csv
import random
import time

# 山东省近似多边形（20个顶点）
sd_coords = [
    (117.500000, 34.400000), (118.350000, 34.850000),
    (119.300000, 34.800000), (120.200000, 34.300000),
    (121.000000, 34.700000), (122.000000, 36.500000),
    (122.700000, 37.400000), (121.800000, 37.600000),
    (120.800000, 37.800000), (119.700000, 37.500000),
    (118.900000, 37.200000), (118.000000, 37.600000),
    (117.200000, 38.200000), (115.800000, 37.800000),
    (115.500000, 37.200000), (115.000000, 36.000000),
    (115.300000, 35.300000), (116.200000, 35.100000),
    (116.800000, 35.600000), (117.400000, 35.400000)
]

# 射线法判断点是否在多边形内（纯Python实现）
def is_point_in_polygon(lon, lat):
    crossings = 0
    for i in range(len(sd_coords)):
        x1, y1 = sd_coords[i]
        x2, y2 = sd_coords[(i+1)%len(sd_coords)]
        if ((y1 > lat) != (y2 > lat)):
            xinters = (lat - y1) * (x2 - x1) / (y2 - y1) + x1
            if lon <= xinters:
                crossings += 1
    return crossings % 2 == 1

# 城市配置（经度，纬度，权重）
cities = {
    '济南': (117.121225, 36.669981, 15),
    '青岛': (120.384428, 36.105215, 25),
    '烟台': (121.453926, 37.470892, 12),
    '潍坊': (119.162349, 36.712502, 10),
    '临沂': (118.362744, 35.110152, 10),
    '济宁': (116.588116, 35.417743, 8),
    '淄博': (118.061325, 36.819084, 7),
    '泰安': (117.089415, 36.202048, 6),
    '威海': (122.127541, 37.516430, 5),
    '德州': (116.304558, 37.462044, 2)
}

# 生成概率分布列表
city_weights = [c[2] for c in cities.values()]
total_weight = sum(city_weights)
probabilities = [w/total_weight for w in city_weights]

# 生成1000个有效点
random.seed(42)
data = []
emotions = ['快乐', '悲伤', '愤怒', '恐惧', '惊奇', '厌恶', '羞耻']

while len(data) < 1000:
    # 按权重随机选择城市
    city = random.choices(list(cities.keys()), weights=probabilities, k=1)[0]
    clon, clat, _ = cities[city]
    
    # 生成随机偏移（标准差动态调整）
    std_dev = 0.1 + 0.1 * (1 - cities[city][2]/25)
    lon = random.gauss(clon, std_dev)
    lat = random.gauss(clat, std_dev)
    
    # 边界快速检查
    if 115.0 <= lon <= 122.7 and 34.3 <= lat <= 38.2:
        # 精确多边形判断
        if is_point_in_polygon(lon, lat):
            # 生成情绪数据
            emotion_idx = random.randint(0, 6)
            row = [round(lon,6), round(lat,6)] + [1 if i == emotion_idx else 0 for i in range(7)]
            data.append(row)

# 写入CSV文件
with open('shandong_emotions.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['lon','lat'] + emotions)
    writer.writerows(data)

print(f"成功生成{len(data)}条数据到 shandong_emotions.csv")