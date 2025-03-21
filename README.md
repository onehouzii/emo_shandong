# 山东省情绪数据分析

这个项目用于分析山东省的情绪数据分布情况。数据包含经纬度信息和情绪类型（1-7）。

## 功能特点

- 情绪分布统计分析
- 空间分布可视化
- 情绪地理中心计算

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 确保数据文件 `shandong_emotion_data.csv` 在当前目录
2. 运行分析脚本：

```bash
python emotion_analysis.py
```

## 输出结果

- `emotion_distribution.png`: 情绪分布柱状图
- `spatial_distribution.png`: 情绪空间分布散点图
- 控制台输出：基本统计信息和地理中心数据

## 数据说明

情绪类型(emo)说明：
- 1-7代表不同的情绪强度
- 数据包含经度(lon)和纬度(lat)信息 