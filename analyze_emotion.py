import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import seaborn as sns
import folium
from folium.plugins import HeatMap
import os
from scipy import stats
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from libpysal.weights import DistanceBand
from esda.moran import Moran
import warnings
warnings.filterwarnings('ignore')

# 创建结果保存路径
RESULTS_DIR = 'analysis_results'
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_csv('emotion_data_2024_all.csv')

# 基本统计分析
def basic_statistics(df):
    # 创建统计结果文本文件
    with open(os.path.join(RESULTS_DIR, 'basic_statistics.txt'), 'w', encoding='utf-8') as f:
        f.write("基本统计信息:\n")
        f.write(f"数据总量: {len(df)}\n\n")
        
        f.write("各类型场所数量:\n")
        f.write(df['类型'].value_counts().to_string())
        f.write("\n\n情绪值统计:\n")
        f.write(df['情绪值'].describe().to_string())
        
        # 不同时间段的平均情绪值
        time_emotion = df.groupby('时间段')['情绪值'].agg(['mean', 'count']).round(2)
        f.write("\n\n各时间段平均情绪值:\n")
        f.write(time_emotion.to_string())
        
    print("基础统计分析完成，结果已保存到", os.path.join(RESULTS_DIR, 'basic_statistics.txt'))

# 绘制情绪值分布直方图
def plot_emotion_distribution(df):
    plt.figure(figsize=(10, 6))
    plt.hist(df['情绪值'], bins=30, edgecolor='black')
    plt.title('情绪值分布')
    plt.xlabel('情绪值')
    plt.ylabel('频次')
    plt.savefig(os.path.join(RESULTS_DIR, 'emotion_distribution.png'))
    plt.close()
    print("情绪值分布图已保存到", os.path.join(RESULTS_DIR, 'emotion_distribution.png'))

# 绘制不同类型场所的情绪箱线图
def plot_emotion_by_type(df):
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='类型', y='情绪值', data=df)
    plt.xticks(rotation=45)
    plt.title('不同类型场所的情绪值分布')
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'emotion_by_type.png'))
    plt.close()
    print("场所类型情绪分布图已保存到", os.path.join(RESULTS_DIR, 'emotion_by_type.png'))

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
    plt.savefig(os.path.join(RESULTS_DIR, 'emotion_by_time.png'))
    plt.close()
    print("时间段情绪变化图已保存到", os.path.join(RESULTS_DIR, 'emotion_by_time.png'))

# 生成热力图
def generate_heatmap(df):
    m = folium.Map(location=[36.8265, 118.0559], zoom_start=11)  # 淄博市中心坐标
    heat_data = [[row['纬度'], row['经度'], row['情绪值']] for index, row in df.iterrows()]
    HeatMap(heat_data).add_to(m)
    m.save(os.path.join(RESULTS_DIR, 'emotion_heatmap.html'))
    print("情绪热力图已保存到", os.path.join(RESULTS_DIR, 'emotion_heatmap.html'))

# 分析不同区域的情绪特征
def analyze_area_emotion(df):
    area_stats = df.groupby('区域')['情绪值'].agg(['mean', 'std', 'count']).round(3)
    
    # 保存区域统计结果
    with open(os.path.join(RESULTS_DIR, 'area_statistics.txt'), 'w', encoding='utf-8') as f:
        f.write("各区域情绪特征:\n")
        f.write(area_stats.to_string())
    
    # 绘制区域情绪箱线图
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='区域', y='情绪值', data=df)
    plt.xticks(rotation=45)
    plt.title('不同区域的情绪值分布')
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'emotion_by_area.png'))
    plt.close()
    print("区域情绪分析结果已保存到", os.path.join(RESULTS_DIR, 'area_statistics.txt'))
    print("区域情绪分布图已保存到", os.path.join(RESULTS_DIR, 'emotion_by_area.png'))

# 导出分析数据
def export_summary_data(df):
    # 计算每个地点的平均情绪值
    location_emotions = df.groupby(['地点名称', '类型', '经度', '纬度'])['情绪值'].agg(['mean', 'count']).round(3)
    location_emotions.to_csv(os.path.join(RESULTS_DIR, 'location_emotions.csv'), encoding='utf-8')
    print("地点情绪数据已导出到", os.path.join(RESULTS_DIR, 'location_emotions.csv'))

def statistical_tests(df):
    """
    进行统计检验分析
    """
    with open(os.path.join(RESULTS_DIR, 'statistical_tests.txt'), 'w', encoding='utf-8') as f:
        # 1. 场所类型的单因素方差分析
        f.write("1. 场所类型情绪差异的单因素方差分析(ANOVA)\n")
        types = df['类型'].unique()
        type_groups = [df[df['类型'] == t]['情绪值'] for t in types]
        f_stat, p_val = stats.f_oneway(*type_groups)
        f.write(f"F统计量: {f_stat:.4f}\n")
        f.write(f"p值: {p_val:.4f}\n")
        
        # 如果ANOVA显著，进行事后检验
        if p_val < 0.05:
            tukey = pairwise_tukeyhsd(df['情绪值'], df['类型'])
            f.write("\n事后检验结果(Tukey HSD):\n")
            f.write(str(tukey))
        
        # 2. 时间段的Kruskal-Wallis检验
        f.write("\n\n2. 时间段情绪差异的Kruskal-Wallis检验\n")
        h_stat, p_val = stats.kruskal(*[df[df['时间段'] == t]['情绪值'] for t in df['时间段'].unique()])
        f.write(f"H统计量: {h_stat:.4f}\n")
        f.write(f"p值: {p_val:.4f}\n")
    
    print("统计检验分析完成，结果已保存到", os.path.join(RESULTS_DIR, 'statistical_tests.txt'))

def spatial_autocorrelation(df):
    """
    空间自相关分析
    """
    # 计算空间权重矩阵
    coords = df[['经度', '纬度']].values
    w = DistanceBand.from_array(coords, threshold=0.01, binary=False)
    w.transform = 'r'
    
    # 计算Moran's I
    moran = Moran(df['情绪值'], w)
    
    with open(os.path.join(RESULTS_DIR, 'spatial_analysis.txt'), 'w', encoding='utf-8') as f:
        f.write("空间自相关分析结果:\n")
        f.write(f"Moran's I: {moran.I:.4f}\n")
        f.write(f"p值: {moran.p_sim:.4f}\n")
        f.write(f"Z分数: {moran.z_sim:.4f}\n")
    
    print("空间自相关分析完成，结果已保存到", os.path.join(RESULTS_DIR, 'spatial_analysis.txt'))

def time_series_analysis(df):
    """
    时间序列分析
    """
    # 计算每天每个时间段的平均情绪值
    daily_emotions = df.groupby(['日期', '时间段'])['情绪值'].mean().unstack()
    
    # 进行时间序列分解
    plt.figure(figsize=(15, 10))
    for col in daily_emotions.columns:
        decomposition = sm.tsa.seasonal_decompose(daily_emotions[col], period=7)
        
        plt.subplot(len(daily_emotions.columns), 1, list(daily_emotions.columns).index(col) + 1)
        decomposition.plot()
        plt.title(f'{col}时段情绪值的时间序列分解')
    
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'time_series_decomposition.png'))
    plt.close()
    
    print("时间序列分析完成，结果已保存到", os.path.join(RESULTS_DIR, 'time_series_decomposition.png'))

def cluster_analysis(df):
    """
    聚类分析
    """
    # 准备聚类特征
    features = ['经度', '纬度', '情绪值']
    X = StandardScaler().fit_transform(df[features])
    
    # 使用肘部法则确定最佳聚类数
    inertias = []
    K = range(1, 11)
    for k in K:
        kmeans = KMeans(n_clusters=k, random_state=42)
        kmeans.fit(X)
        inertias.append(kmeans.inertia_)
    
    # 绘制肘部图
    plt.figure(figsize=(10, 6))
    plt.plot(K, inertias, 'bx-')
    plt.xlabel('k值')
    plt.ylabel('簇内平方和')
    plt.title('确定最佳聚类数的肘部图')
    plt.savefig(os.path.join(RESULTS_DIR, 'elbow_plot.png'))
    plt.close()
    
    # 执行最终聚类
    optimal_k = 4  # 根据肘部图确定
    kmeans = KMeans(n_clusters=optimal_k, random_state=42)
    df['cluster'] = kmeans.fit_predict(X)
    
    # 绘制聚类结果地图
    m = folium.Map(location=[36.8265, 118.0559], zoom_start=11)
    colors = ['red', 'blue', 'green', 'purple']
    
    for idx, row in df.iterrows():
        folium.CircleMarker(
            location=[row['纬度'], row['经度']],
            radius=5,
            color=colors[row['cluster']],
            popup=f"情绪值: {row['情绪值']:.2f}\n类型: {row['类型']}",
            fill=True
        ).add_to(m)
    
    m.save(os.path.join(RESULTS_DIR, 'cluster_map.html'))
    
    # 保存聚类统计信息
    cluster_stats = df.groupby('cluster').agg({
        '情绪值': ['mean', 'std', 'count'],
        '类型': lambda x: x.value_counts().index[0],
        '时间段': lambda x: x.value_counts().index[0]
    }).round(3)
    
    cluster_stats.to_csv(os.path.join(RESULTS_DIR, 'cluster_statistics.csv'))
    print("聚类分析完成，结果已保存到", os.path.join(RESULTS_DIR, 'cluster_statistics.csv'))

def confidence_intervals(df):
    """
    计算情绪值的置信区间
    """
    print("计算情绪值的95%置信区间...")
    ci = stats.t.interval(
        confidence=0.95,  # 使用confidence而不是alpha
        df=len(df['情绪值'])-1,
        loc=np.mean(df['情绪值']),
        scale=stats.sem(df['情绪值'])
    )
    
    with open(os.path.join(RESULTS_DIR, 'confidence_intervals.txt'), 'w', encoding='utf-8') as f:
        f.write(f"情绪值的95%置信区间:\n")
        f.write(f"下限: {ci[0]:.4f}\n")
        f.write(f"上限: {ci[1]:.4f}\n")
        f.write(f"平均值: {np.mean(df['情绪值']):.4f}\n")
        f.write(f"标准误: {stats.sem(df['情绪值']):.4f}\n")
    
    print("置信区间分析完成，结果已保存到", os.path.join(RESULTS_DIR, 'confidence_intervals.txt'))

if __name__ == "__main__":
    print("开始数据分析...")
    # 执行基础分析
    basic_statistics(df)
    plot_emotion_distribution(df)
    plot_emotion_by_type(df)
    plot_emotion_by_time(df)
    generate_heatmap(df)
    analyze_area_emotion(df)
    export_summary_data(df)
    
    # 执行高级统计分析
    statistical_tests(df)
    spatial_autocorrelation(df)
    time_series_analysis(df)
    cluster_analysis(df)
    confidence_intervals(df)
    
    print("\n分析完成！所有结果已保存到", RESULTS_DIR, "文件夹中") 