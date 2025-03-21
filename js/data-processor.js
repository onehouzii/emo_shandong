// 数据处理工具类
class EmotionDataProcessor {
    constructor() {
        this.cache = new Map(); // 缓存已加载的数据
        this.timeSlots = ['深夜', '凌晨', '早上', '上午', '中午', '下午', '傍晚', '晚上'];
        this.districts = new Set(); // 存储所有区域
        this.poiTypes = new Set();  // 存储所有POI类型
    }

    // 加载指定月份的数据
    async loadMonthData(month) {
        if (this.cache.has(month)) {
            return this.cache.get(month);
        }

        try {
            // 修改文件路径格式以匹配实际文件名
            const filename = month === 'all' ? 'emotion_data_2024_all.csv' : `emotion_data_2024${month}.csv`;
            const response = await fetch(`data/${filename}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const text = await response.text();
            const data = this.parseCSV(text);
            this.cache.set(month, data);
            
            // 更新区域和POI类型集合
            data.forEach(record => {
                this.districts.add(record.区域);
                this.poiTypes.add(record.类型);
            });
            
            return data;
        } catch (error) {
            console.error('加载数据失败:', error);
            return [];
        }
    }

    // 解析CSV数据
    parseCSV(text) {
        const lines = text.trim().split('\n');
        const headers = lines[0].split(',');
        
        return lines.slice(1).map(line => {
            const values = line.split(',');
            const record = {};
            headers.forEach((header, index) => {
                record[header] = values[index]?.trim();
            });
            return record;
        });
    }

    // 计算热力图数据
    calculateHeatmapData(data) {
        return data.map(record => ({
            lat: parseFloat(record.纬度),
            lng: parseFloat(record.经度),
            intensity: this.calculateIntensity(record)
        })).filter(point => !isNaN(point.lat) && !isNaN(point.lng));
    }

    // 计算情绪强度
    calculateIntensity(record) {
        return parseFloat(record.情绪值) / 10; // 归一化情绪值
    }

    // 计算空间统计数据
    calculateSpatialStats(data) {
        const stats = {
            highDensity: 0,
            mediumDensity: 0,
            lowDensity: 0,
            districtStats: {},
            timeSlotStats: {},
            poiTypeStats: {}
        };

        // 计算每个区域的统计数据
        data.forEach(record => {
            // 区域统计
            if (!stats.districtStats[record.区域]) {
                stats.districtStats[record.区域] = {
                    count: 0,
                    avgEmotion: 0,
                    emotions: []
                };
            }
            stats.districtStats[record.区域].count++;
            stats.districtStats[record.区域].emotions.push(parseFloat(record.情绪值));

            // 时间段统计
            if (!stats.timeSlotStats[record.时间段]) {
                stats.timeSlotStats[record.时间段] = {
                    count: 0,
                    avgEmotion: 0,
                    emotions: []
                };
            }
            stats.timeSlotStats[record.时间段].count++;
            stats.timeSlotStats[record.时间段].emotions.push(parseFloat(record.情绪值));

            // POI类型统计
            if (!stats.poiTypeStats[record.类型]) {
                stats.poiTypeStats[record.类型] = {
                    count: 0,
                    avgEmotion: 0,
                    emotions: []
                };
            }
            stats.poiTypeStats[record.类型].count++;
            stats.poiTypeStats[record.类型].emotions.push(parseFloat(record.情绪值));
        });

        // 计算平均情绪值
        Object.values(stats.districtStats).forEach(stat => {
            stat.avgEmotion = stat.emotions.reduce((a, b) => a + b, 0) / stat.emotions.length;
        });
        Object.values(stats.timeSlotStats).forEach(stat => {
            stat.avgEmotion = stat.emotions.reduce((a, b) => a + b, 0) / stat.emotions.length;
        });
        Object.values(stats.poiTypeStats).forEach(stat => {
            stat.avgEmotion = stat.emotions.reduce((a, b) => a + b, 0) / stat.emotions.length;
        });

        // 计算密度区域统计
        const totalLocations = new Set(data.map(r => `${r.经度},${r.纬度}`)).size;
        stats.highDensity = Math.floor(totalLocations * 0.3);
        stats.mediumDensity = Math.floor(totalLocations * 0.3);
        stats.lowDensity = totalLocations - stats.highDensity - stats.mediumDensity;

        return stats;
    }

    // 计算时空演变数据
    calculateTemporalTrend(data) {
        const trend = new Map();
        
        // 按日期和时间段统计数据
        data.forEach(record => {
            const date = record.日期;
            if (!trend.has(date)) {
                trend.set(date, {
                    count: 0,
                    avgEmotion: 0,
                    emotions: []
                });
            }
            trend.get(date).count++;
            trend.get(date).emotions.push(parseFloat(record.情绪值));
        });

        // 计算每天的平均情绪值
        trend.forEach(value => {
            value.avgEmotion = value.emotions.reduce((a, b) => a + b, 0) / value.emotions.length;
        });

        return Array.from(trend.entries())
            .sort(([a], [b]) => new Date(a) - new Date(b))
            .map(([date, stats]) => ({
                date,
                count: stats.count,
                avgEmotion: stats.avgEmotion
            }));
    }

    // 执行空间聚类分析
    performClusterAnalysis(data, numberOfClusters = 5) {
        const points = data.map(record => ({
            type: 'Feature',
            properties: {
                name: record.地点名称,
                type: record.类型,
                emotion: parseFloat(record.情绪值),
                district: record.区域
            },
            geometry: {
                type: 'Point',
                coordinates: [parseFloat(record.经度), parseFloat(record.纬度)]
            }
        }));

        return turf.clustersKmeans(turf.featureCollection(points), {
            numberOfClusters,
            mutate: true
        });
    }

    // 生成缓冲区分析数据
    generateBufferZones(data, radius = 0.5) {
        // 按地点名称分组
        const locations = new Map();
        data.forEach(record => {
            const key = `${record.地点名称}_${record.经度}_${record.纬度}`;
            if (!locations.has(key)) {
                locations.set(key, {
                    name: record.地点名称,
                    type: record.类型,
                    coordinates: [parseFloat(record.经度), parseFloat(record.纬度)],
                    emotions: []
                });
            }
            locations.get(key).emotions.push(parseFloat(record.情绪值));
        });

        // 为每个位置生成缓冲区
        return Array.from(locations.values()).map(location => {
            const avgEmotion = location.emotions.reduce((a, b) => a + b, 0) / location.emotions.length;
            const point = turf.point(location.coordinates, {
                name: location.name,
                type: location.type,
                avgEmotion: avgEmotion
            });
            return turf.buffer(point, radius, {units: 'kilometers'});
        });
    }

    // 执行核密度分析
    performKernelDensity(data, cellSize = 0.01, radius = 0.5) {
        const points = data.map(record => ({
            type: 'Feature',
            properties: {
                weight: parseFloat(record.情绪值)
            },
            geometry: {
                type: 'Point',
                coordinates: [parseFloat(record.经度), parseFloat(record.纬度)]
            }
        }));

        // 创建包围盒
        const bbox = turf.bbox(turf.featureCollection(points));
        const options = {
            gridType: 'square',
            property: 'weight',
            units: 'kilometers',
            cellSize: cellSize,
            radius: radius
        };

        return turf.pointGrid(bbox, cellSize, options);
    }

    // 执行空间自相关分析（Moran's I）
    calculateSpatialAutocorrelation(data) {
        const points = data.map(record => ({
            coordinates: [parseFloat(record.经度), parseFloat(record.纬度)],
            value: parseFloat(record.情绪值)
        }));

        let totalWeight = 0;
        let n = points.length;
        let mean = points.reduce((sum, p) => sum + p.value, 0) / n;
        let numerator = 0;
        let denominator = 0;

        // 计算空间权重和自相关
        for (let i = 0; i < n; i++) {
            for (let j = 0; j < n; j++) {
                if (i !== j) {
                    // 计算距离作为权重
                    let distance = turf.distance(
                        turf.point(points[i].coordinates),
                        turf.point(points[j].coordinates)
                    );
                    let weight = 1 / (distance + 0.0001); // 避免除以0
                    totalWeight += weight;

                    numerator += weight * (points[i].value - mean) * (points[j].value - mean);
                }
            }
            denominator += Math.pow(points[i].value - mean, 2);
        }

        // 计算Moran's I指数
        const moranI = (n / totalWeight) * (numerator / denominator);
        
        return {
            moranI,
            interpretation: this.interpretMoranI(moranI)
        };
    }

    // 解释Moran's I值
    interpretMoranI(moranI) {
        if (moranI > 0.3) {
            return '存在显著的正空间自相关，情绪值呈现空间聚集性';
        } else if (moranI < -0.3) {
            return '存在显著的负空间自相关，情绪值呈现空间分散性';
        } else {
            return '空间自相关性不显著，情绪值分布较为随机';
        }
    }

    // 生成泰森多边形
    generateVoronoiPolygons(data) {
        const points = data.map(record => ({
            type: 'Feature',
            properties: {
                name: record.地点名称,
                emotion: parseFloat(record.情绪值),
                type: record.类型
            },
            geometry: {
                type: 'Point',
                coordinates: [parseFloat(record.经度), parseFloat(record.纬度)]
            }
        }));

        const options = {
            bbox: [117.5, 36.0, 118.5, 37.5] // 淄博市大致范围
        };

        return turf.voronoi(turf.featureCollection(points), options);
    }

    // 执行空间插值分析（IDW方法）
    performIDWInterpolation(data, cellSize = 0.01) {
        const points = data.map(record => ({
            coordinates: [parseFloat(record.经度), parseFloat(record.纬度)],
            value: parseFloat(record.情绪值)
        }));

        // 创建网格
        const bbox = [117.5, 36.0, 118.5, 37.5]; // 淄博市大致范围
        const grid = turf.pointGrid(bbox, cellSize);

        // 对每个网格点进行IDW插值
        return grid.features.map(cell => {
            const cellCoord = cell.geometry.coordinates;
            let weightedSum = 0;
            let weightSum = 0;

            points.forEach(point => {
                const distance = turf.distance(
                    turf.point(cellCoord),
                    turf.point(point.coordinates)
                );
                const weight = 1 / Math.pow(distance + 0.0001, 2); // 平方反比权重
                weightedSum += weight * point.value;
                weightSum += weight;
            });

            return {
                type: 'Feature',
                properties: {
                    interpolated: weightedSum / weightSum
                },
                geometry: cell.geometry
            };
        });
    }

    // 路网分析（计算可达性）
    calculateAccessibility(data, radius = 1) {
        const points = data.map(record => ({
            type: 'Feature',
            properties: {
                name: record.地点名称,
                emotion: parseFloat(record.情绪值)
            },
            geometry: {
                type: 'Point',
                coordinates: [parseFloat(record.经度), parseFloat(record.纬度)]
            }
        }));

        // 为每个点创建服务区
        const serviceAreas = points.map(point => {
            const buffer = turf.buffer(point, radius, {units: 'kilometers'});
            buffer.properties = {
                ...point.properties,
                radius: radius
            };
            return buffer;
        });

        // 计算覆盖区域
        const union = turf.union(...serviceAreas);
        
        // 计算可达性指标
        const accessibility = {
            totalArea: turf.area(union) / 1000000, // 转换为平方公里
            coveragePoints: points.length,
            averageEmotion: points.reduce((sum, p) => sum + p.properties.emotion, 0) / points.length
        };

        return {
            serviceAreas: turf.featureCollection(serviceAreas),
            union,
            accessibility
        };
    }

    // 获取所有区域
    getDistricts() {
        return Array.from(this.districts);
    }

    // 获取所有POI类型
    getPoiTypes() {
        return Array.from(this.poiTypes);
    }
}

// 导出数据处理器实例
window.dataProcessor = new EmotionDataProcessor(); 