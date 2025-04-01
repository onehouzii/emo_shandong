import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import folium
from folium.plugins import HeatMap

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
poi_data = pd.read_csv('淄博poi.csv')
emotion_data = pd.read_csv('emotion_data_2024_all.csv')

# 1. 场所类型分布图
def create_place_distribution():
    place_counts = poi_data['type'].value_counts()
    plt.figure(figsize=(12, 6))
    place_counts.plot(kind='bar')
    plt.title('淄博市各类场所数量分布')
    plt.xlabel('场所类型')
    plt.ylabel('数量')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('place_distribution.png')
    plt.close()

# 2. 情绪时间分布图
def create_emotion_time_distribution():
    emotion_data['hour'] = pd.to_datetime(emotion_data['time']).dt.hour
    hourly_emotion = emotion_data.groupby('hour')['emotion_value'].mean()
    
    plt.figure(figsize=(12, 6))
    hourly_emotion.plot(kind='line', marker='o')
    plt.title('淄博市情绪时间分布特征')
    plt.xlabel('时间（小时）')
    plt.ylabel('平均情绪值')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('emotion_time_distribution.png')
    plt.close()

# 3. 情绪空间分布热力图
def create_emotion_heatmap():
    # 创建地图中心点（淄博市中心坐标）
    center = [36.8131, 118.0548]
    m = folium.Map(location=center, zoom_start=12)
    
    # 准备热力图数据
    heat_data = emotion_data[['latitude', 'longitude', 'emotion_value']].values.tolist()
    
    # 添加热力图层
    HeatMap(heat_data).add_to(m)
    
    # 保存地图
    m.save('emotion_heatmap.html')

# 4. 情绪分布箱线图
def create_emotion_boxplot():
    plt.figure(figsize=(10, 6))
    sns.boxplot(y=emotion_data['emotion_value'])
    plt.title('淄博市情绪分布箱线图')
    plt.ylabel('情绪值')
    plt.tight_layout()
    plt.savefig('emotion_boxplot.png')
    plt.close()

# 5. 情绪聚类分析结果
def create_emotion_clustering():
    # 使用K-means聚类
    from sklearn.cluster import KMeans
    kmeans = KMeans(n_clusters=3, random_state=42)
    emotion_data['cluster'] = kmeans.fit_predict(emotion_data[['emotion_value']])
    
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='cluster', y='emotion_value', data=emotion_data)
    plt.title('淄博市情绪聚类分析结果')
    plt.xlabel('聚类类别')
    plt.ylabel('情绪值')
    plt.tight_layout()
    plt.savefig('emotion_clustering.png')
    plt.close()

# 6. 商业场所情绪分布
def create_commercial_emotion():
    commercial_data = emotion_data[emotion_data['place_type'] == '商业']
    plt.figure(figsize=(10, 6))
    sns.boxplot(y=commercial_data['emotion_value'])
    plt.title('商业场所情绪分布特征')
    plt.ylabel('情绪值')
    plt.tight_layout()
    plt.savefig('commercial_emotion.png')
    plt.close()

# 7. 文化场所情绪分布
def create_cultural_emotion():
    cultural_data = emotion_data[emotion_data['place_type'] == '文化']
    plt.figure(figsize=(10, 6))
    sns.boxplot(y=cultural_data['emotion_value'])
    plt.title('文化场所情绪分布特征')
    plt.ylabel('情绪值')
    plt.tight_layout()
    plt.savefig('cultural_emotion.png')
    plt.close()

# 8. 休闲场所情绪分布
def create_recreational_emotion():
    recreational_data = emotion_data[emotion_data['place_type'] == '休闲']
    plt.figure(figsize=(10, 6))
    sns.boxplot(y=recreational_data['emotion_value'])
    plt.title('休闲场所情绪分布特征')
    plt.ylabel('情绪值')
    plt.tight_layout()
    plt.savefig('recreational_emotion.png')
    plt.close()

# 生成所有图表
def generate_all_charts():
    create_place_distribution()
    create_emotion_time_distribution()
    create_emotion_heatmap()
    create_emotion_boxplot()
    create_emotion_clustering()
    create_commercial_emotion()
    create_cultural_emotion()
    create_recreational_emotion()

if __name__ == '__main__':
    generate_all_charts() 