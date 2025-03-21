import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
import jieba
import jieba.analyse
from snownlp import SnowNLP
import folium
from folium.plugins import HeatMap
import matplotlib.pyplot as plt
from scipy import stats
import seaborn as sns
from collections import Counter
import json
import os
from sklearn.cluster import KMeans
import matplotlib as mpl

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

class NumpyEncoder(json.JSONEncoder):
    """ 处理 NumPy 数据类型的 JSON 编码器 """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

class EmotionAnalyzer:
    def __init__(self):
        self.df = pd.read_csv('shandong_emotion_data.csv')
        # 确保static目录存在
        if not os.path.exists('static'):
            os.makedirs('static')
        
    def preprocess_data(self):
        """数据预处理"""
        # 确保经纬度数据有效
        self.df = self.df.dropna(subset=['lon', 'lat', 'emo'])
        # 将情绪值归一化到[0,1]区间
        self.df['emo_normalized'] = (self.df['emo'] - self.df['emo'].min()) / (self.df['emo'].max() - self.df['emo'].min())
        
    def analyze_spatial_distribution(self):
        """空间分布分析"""
        # 使用K-means聚类分析情绪空间分布
        X = self.df[['lat', 'lon']].values
        kmeans = KMeans(n_clusters=5, random_state=42)
        self.df['cluster'] = kmeans.fit_predict(X)
        
        # 计算每个聚类的平均情绪值
        cluster_emotions = self.df.groupby('cluster')['emo'].agg(['mean', 'std', 'count']).round(3)
        
        # 生成聚类散点图
        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(self.df['lon'], self.df['lat'], 
                            c=self.df['emo'], cmap='RdYlBu',
                            alpha=0.6)
        plt.colorbar(scatter, label='情绪值')
        plt.title('山东省情绪空间分布')
        plt.xlabel('经度')
        plt.ylabel('纬度')
        plt.savefig('static/spatial_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 转换为可序列化的字典
        result = {}
        for idx, row in cluster_emotions.iterrows():
            result[f"聚类{idx}"] = {
                '平均值': float(row['mean']),
                '标准差': float(row['std']),
                '样本数': int(row['count'])
            }
        return result
    
    def analyze_emotion_distribution(self):
        """情绪分布分析"""
        # 生成情绪值分布直方图
        plt.figure(figsize=(10, 6))
        sns.histplot(data=self.df, x='emo', bins=30, kde=True)
        plt.title('情绪值分布')
        plt.xlabel('情绪值')
        plt.ylabel('频次')
        plt.savefig('static/emotion_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 计算基本统计量
        stats_dict = {
            '平均值': float(self.df['emo'].mean()),
            '中位数': float(self.df['emo'].median()),
            '标准差': float(self.df['emo'].std()),
            '偏度': float(self.df['emo'].skew()),
            '峰度': float(self.df['emo'].kurtosis())
        }
        
        return stats_dict
    
    def analyze_regional_patterns(self):
        """区域模式分析"""
        # 将经纬度网格化，分析区域情绪特征
        self.df['lat_grid'] = self.df['lat'].round(1)
        self.df['lon_grid'] = self.df['lon'].round(1)
        
        # 计算网格区域平均情绪值
        regional_emotions = self.df.groupby(['lat_grid', 'lon_grid'])['emo'].agg(['mean', 'count'])
        regional_emotions = regional_emotions[regional_emotions['count'] > 5]  # 过滤样本数过少的区域
        
        # 生成区域情绪箱型图
        plt.figure(figsize=(12, 6))
        sns.boxplot(data=self.df, x='lat_grid', y='emo')
        plt.title('不同纬度区域情绪分布')
        plt.xticks(rotation=45)
        plt.xlabel('纬度')
        plt.ylabel('情绪值')
        plt.tight_layout()
        plt.savefig('static/regional_patterns.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 转换为可序列化的字典
        result = {}
        for idx, row in regional_emotions.iterrows():
            key = f"区域({float(idx[0])},{float(idx[1])})"
            result[key] = {
                '平均情绪值': float(row['mean']),
                '样本数量': int(row['count'])
            }
        
        return result
    
    def analyze_emotion_correlations(self):
        """情绪相关性分析"""
        # 计算情绪值与地理位置的相关性
        correlations = {
            '经度相关性': float(stats.pearsonr(self.df['lon'], self.df['emo'])[0]),
            '纬度相关性': float(stats.pearsonr(self.df['lat'], self.df['emo'])[0])
        }
        
        # 生成相关性热力图
        corr_matrix = self.df[['lon', 'lat', 'emo']].corr()
        plt.figure(figsize=(8, 6))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
        plt.title('变量相关性热力图')
        plt.tight_layout()
        plt.savefig('static/correlations.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        return correlations
    
    def generate_report(self):
        """生成综合分析报告"""
        report = {
            "数据概况": {
                "样本总量": int(len(self.df)),
                "经度范围": [float(self.df['lon'].min()), float(self.df['lon'].max())],
                "纬度范围": [float(self.df['lat'].min()), float(self.df['lat'].max())],
                "情绪值范围": [float(self.df['emo'].min()), float(self.df['emo'].max())]
            },
            "情绪分布统计": self.analyze_emotion_distribution(),
            "空间聚类分析": self.analyze_spatial_distribution(),
            "区域模式分析": self.analyze_regional_patterns(),
            "相关性分析": self.analyze_emotion_correlations()
        }
        
        return report

def main():
    # 初始化分析器
    analyzer = EmotionAnalyzer()
    analyzer.preprocess_data()
    
    # 生成分析报告
    report = analyzer.generate_report()
    
    # 将报告保存为JSON文件
    with open('static/analysis_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
    
    print("分析完成！报告和可视化结果已保存到static目录。")
    
    # 打印报告内容
    print("\n分析报告概要：")
    print(f"样本总量：{report['数据概况']['样本总量']}")
    print(f"情绪值范围：{report['数据概况']['情绪值范围']}")
    print(f"平均情绪值：{report['情绪分布统计']['平均值']:.2f}")
    print(f"情绪标准差：{report['情绪分布统计']['标准差']:.2f}")
    print(f"经度相关性：{report['相关性分析']['经度相关性']:.3f}")
    print(f"纬度相关性：{report['相关性分析']['纬度相关性']:.3f}")

if __name__ == "__main__":
    main() 