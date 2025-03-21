import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.font_manager import FontProperties
import numpy as np
import os
import sys

def load_data(file_path):
    try:
        # 获取脚本所在目录的绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建数据文件的完整路径
        data_path = os.path.join(script_dir, file_path)
        
        if not os.path.exists(data_path):
            print(f"错误：找不到数据文件 '{data_path}'")
            print("请确保数据文件与脚本在同一目录下。")
            sys.exit(1)
            
        return pd.read_csv(data_path)
    except Exception as e:
        print(f"读取数据文件时出错：{str(e)}")
        sys.exit(1)

def setup_plotting():
    # 设置中文字体和样式
    try:
        plt.style.use('seaborn')
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
    except Exception as e:
        print(f"警告：设置绘图样式时出现问题：{str(e)}")

def analyze_emotion_distribution(df):
    try:
        # 计算情绪分布
        emotion_counts = df['emo'].value_counts().sort_index()
        
        # 创建柱状图
        plt.figure(figsize=(12, 6))
        ax = emotion_counts.plot(kind='bar', color='skyblue')
        plt.title('山东省情绪分布', fontsize=14, pad=15)
        plt.xlabel('情绪类型', fontsize=12)
        plt.ylabel('数量', fontsize=12)
        
        # 添加数值标签
        for i, v in enumerate(emotion_counts):
            ax.text(i, v, str(v), ha='center', va='bottom')
        
        # 添加网格线
        plt.grid(True, axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig('emotion_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 打印统计信息
        print("\n情绪分布统计：")
        print(emotion_counts)
        print("\n基本统计量：")
        print(df['emo'].describe())
        
        # 计算情绪比例
        emotion_percentages = (emotion_counts / len(df) * 100).round(2)
        print("\n情绪类型占比（%）：")
        print(emotion_percentages)
        
    except Exception as e:
        print(f"分析情绪分布时出错：{str(e)}")

def analyze_spatial_distribution(df):
    try:
        # 创建散点图展示情绪的空间分布
        plt.figure(figsize=(14, 10))
        scatter = plt.scatter(df['lon'], df['lat'], 
                            c=df['emo'], 
                            cmap='RdYlBu', 
                            alpha=0.6,
                            s=100)  # 增大点的大小
        
        # 添加颜色条
        cbar = plt.colorbar(scatter)
        cbar.set_label('情绪类型', fontsize=12)
        
        # 设置标题和轴标签
        plt.title('山东省情绪空间分布', fontsize=14, pad=15)
        plt.xlabel('经度', fontsize=12)
        plt.ylabel('纬度', fontsize=12)
        
        # 添加网格线
        plt.grid(True, linestyle='--', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('spatial_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    except Exception as e:
        print(f"分析空间分布时出错：{str(e)}")

def analyze_emotion_clusters(df):
    try:
        # 计算每种情绪的地理中心和统计信息
        emotion_centers = df.groupby('emo').agg({
            'lon': ['mean', 'min', 'max'],
            'lat': ['mean', 'min', 'max'],
            'emo': 'count'
        })
        
        # 重命名列
        emotion_centers.columns = ['经度_平均', '经度_最小', '经度_最大',
                                 '纬度_平均', '纬度_最小', '纬度_最大',
                                 '样本数量']
        
        print("\n各情绪类型的地理分布特征：")
        print(emotion_centers.round(4))
        
        # 计算情绪空间分布的集中度
        print("\n情绪空间分布范围：")
        for emo in sorted(df['emo'].unique()):
            emo_data = df[df['emo'] == emo]
            lon_range = emo_data['lon'].max() - emo_data['lon'].min()
            lat_range = emo_data['lat'].max() - emo_data['lat'].min()
            print(f"\n情绪类型 {emo}:")
            print(f"经度范围：{lon_range:.4f}°")
            print(f"纬度范围：{lat_range:.4f}°")
            
    except Exception as e:
        print(f"分析情绪聚类时出错：{str(e)}")

def main():
    print("开始分析山东省情绪数据...")
    
    # 加载数据
    df = load_data('shandong_emotion_data.csv')
    
    # 设置绘图参数
    setup_plotting()
    
    # 执行分析
    analyze_emotion_distribution(df)
    analyze_spatial_distribution(df)
    analyze_emotion_clusters(df)
    
    print("\n分析完成！可视化结果已保存为PNG文件。")

if __name__ == "__main__":
    main() 