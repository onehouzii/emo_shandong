import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import seaborn as sns
import folium
from folium.plugins import HeatMap

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_csv('emotion_data_2024_all.csv')

# 基本统计分析
def basic_statistics(df):
    print("\n基本统计信息:")
    print(f"数据总量: {len(df)}")
    print("\n各类型场所数量:")
    print(df['类型'].value_counts())
    print("\n情绪值统计:")
    print(df['情绪值'].describe())
    
    # 不同时间段的平均情绪值
    time_emotion = df.groupby('时间段')['情绪值'].agg(['mean', 'count']).round(2)
    print("\n各时间段平均情绪值:")
    print(time_emotion)

# 绘制情绪值分布直方图
def plot_emotion_distribution(df):
    plt.figure(figsize=(10, 6))
    plt.hist(df['情绪值'], bins=30, edgecolor='black')
    plt.title('情绪值分布')
    plt.xlabel('情绪值')
    plt.ylabel('频次')
    plt.savefig('emotion_distribution.png')
    plt.close()

# 绘制不同类型场所的情绪箱线图
def plot_emotion_by_type(df):
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='类型', y='情绪值', data=df)
    plt.xticks(rotation=45)
    plt.title('不同类型场所的情绪值分布')
    plt.tight_layout()
    plt.savefig('emotion_by_type.png')
    plt.close()

# 绘制时间段情绪变化
def plot_emotion_by_time(df):
    time_order = ['凌晨', '上午', '中午', '下午', '傍晚', '晚上', '深夜']
    time_emotion = df.groupby('时间段')['情绪值'].mean().reindex(time_order)
    
    plt.figure(figsize=(10, 6))
    time_emotion.plot(kind='line', marker='o')
    plt.title('各时间段平均情绪值变化')
    plt.xlabel('时间段')
    plt.ylabel('平均情绪值')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('emotion_by_time.png')
    plt.close()

# 生成热力图
def generate_heatmap(df):
    m = folium.Map(location=[36.8265, 118.0559], zoom_start=11)  # 淄博市中心坐标
    heat_data = [[row['纬度'], row['经度'], row['情绪值']] for index, row in df.iterrows()]
    HeatMap(heat_data).add_to(m)
    m.save('emotion_heatmap.html')

# 分析不同区域的情绪特征
def analyze_area_emotion(df):
    area_stats = df.groupby('区域')['情绪值'].agg(['mean', 'std', 'count']).round(3)
    print("\n各区域情绪特征:")
    print(area_stats)
    
    # 绘制区域情绪箱线图
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='区域', y='情绪值', data=df)
    plt.xticks(rotation=45)
    plt.title('不同区域的情绪值分布')
    plt.tight_layout()
    plt.savefig('emotion_by_area.png')
    plt.close()

if __name__ == "__main__":
    # 执行分析
    basic_statistics(df)
    plot_emotion_distribution(df)
    plot_emotion_by_type(df)
    plot_emotion_by_time(df)
    generate_heatmap(df)
    analyze_area_emotion(df) 