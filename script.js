// 常量定义
const CONFIG = {
    CESIUM_TOKEN: window.CESIUM_ACCESS_TOKEN,
    MAP_CENTER: [117.0, 36.6],
    MAP_ZOOM: 7,
    AMAP_KEY: '30d50b04a7a13603c1ecc1cec2d2c66b',
    ANIMATION_DURATION: 2000,
    UPDATE_INTERVAL: 60000, // 1分钟更新一次
    CITIES: [
        { name: '济南', location: [117.000923, 36.675807] },
        { name: '青岛', location: [120.355173, 36.082982] },
        { name: '淄博', location: [118.047648, 36.814939] },
        { name: '枣庄', location: [117.557964, 34.856424] },
        { name: '东营', location: [118.66471, 37.434564] },
        { name: '烟台', location: [121.391382, 37.539297] },
        { name: '潍坊', location: [119.107078, 36.70925] },
        { name: '济宁', location: [116.587245, 35.415393] },
        { name: '泰安', location: [117.129063, 36.194968] },
        { name: '威海', location: [122.116394, 37.509691] },
        { name: '日照', location: [119.461208, 35.428588] },
        { name: '临沂', location: [118.326443, 35.065282] },
        { name: '德州', location: [116.307428, 37.453968] },
        { name: '聊城', location: [115.980367, 36.456013] },
        { name: '滨州', location: [118.016974, 37.383542] },
        { name: '菏泽', location: [115.469381, 35.246531] }
    ]
};

// 工具函数
const utils = {
    generateRandomValue: (min, max) => Math.random() * (max - min) + min,
    
    formatTime: (hours) => `${hours.toString().padStart(2, '0')}:00`,
    
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// 地图控制器
class MapController {
    constructor() {
        this.viewer = null;
        this.scene = null;
        this.heatmapLayer = null;
        this.init();
    }

    init() {
        // 初始化 Cesium
        this.initCesium();
        // 初始化 L7 场景
        this.initL7Scene();
        // 添加事件监听
        this.addEventListeners();
        // 开始定时更新
        this.startAutoUpdate();
    }

    initCesium() {
        this.viewer = new Cesium.Viewer('cesiumContainer', {
            terrainProvider: Cesium.createWorldTerrain(),
            baseLayerPicker: false,
            geocoder: false,
            homeButton: true,
            sceneModePicker: true,
            navigationHelpButton: false,
            animation: false,
            timeline: false,
            fullscreenButton: true,
            scene3DOnly: true
        });

        // 移除默认图层并添加高德地图
        this.viewer.imageryLayers.removeAll();
        const gaodeImageryProvider = new Cesium.UrlTemplateImageryProvider({
            url: 'https://webst02.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}',
            minimumLevel: 3,
            maximumLevel: 18
        });
        this.viewer.imageryLayers.addImageryProvider(gaodeImageryProvider);

        // 设置初始视角
        this.flyToShandong();
    }

    initL7Scene() {
        this.scene = new L7.Scene({
            id: 'cesiumContainer',
            map: new L7.AMap({
                pitch: 0,
                style: 'dark',
                center: CONFIG.MAP_CENTER,
                zoom: CONFIG.MAP_ZOOM,
                token: CONFIG.AMAP_KEY,
                plugin: ['AMap.Scale', 'AMap.ToolBar']
            })
        });

        this.scene.on('loaded', () => this.initHeatmap());
    }

    initHeatmap() {
        const data = this.generateHeatmapData();
        this.heatmapLayer = new L7.HeatmapLayer({
            data,
            size: 50,
            shape: 'circle',
            blend: 'normal',
            field: 'value',
            style: {
                intensity: 3,
                radius: 30,
                opacity: 0.8,
                colorsRamp: [
                    { color: '#0A1930', position: 0 },
                    { color: '#1B4B82', position: 0.2 },
                    { color: '#2B7DE1', position: 0.4 },
                    { color: '#6A11CB', position: 0.6 },
                    { color: '#FFD700', position: 0.8 },
                    { color: '#FF4500', position: 1.0 }
                ]
            }
        });

        this.scene.addLayer(this.heatmapLayer);
    }

    generateHeatmapData(dataType = 'emotion') {
        return {
            type: 'FeatureCollection',
            features: CONFIG.CITIES.map(city => ({
                type: 'Feature',
                properties: {
                    value: this.getValueByType(dataType),
                    name: city.name
                },
                geometry: {
                    type: 'Point',
                    coordinates: city.location
                }
            }))
        };
    }

    getValueByType(dataType) {
        switch(dataType) {
            case 'emotion':
                return utils.generateRandomValue(0.2, 1);
            case 'temperature':
                return utils.generateRandomValue(10, 40);
            case 'population':
                return utils.generateRandomValue(100, 600);
            default:
                return utils.generateRandomValue(0, 1);
        }
    }

    flyToShandong() {
        this.viewer.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(...CONFIG.MAP_CENTER, 800000),
            orientation: {
                heading: 0.0,
                pitch: -Cesium.Math.PI_OVER_FOUR,
                roll: 0.0
            },
            duration: CONFIG.ANIMATION_DURATION / 1000
        });
    }

    updateHeatmap(dataType) {
        const data = this.generateHeatmapData(dataType);
        this.heatmapLayer?.setData(data);
    }

    addEventListeners() {
        const dataTypeSelect = document.getElementById('dataType');
        const timeRange = document.getElementById('timeRange');
        const timeValue = document.getElementById('timeValue');

        if (dataTypeSelect) {
            dataTypeSelect.addEventListener('change', () => {
                this.updateHeatmap(dataTypeSelect.value);
            });
        }

        if (timeRange) {
            timeRange.addEventListener('input', (e) => {
                const hours = e.target.value;
                if (timeValue) {
                    timeValue.textContent = utils.formatTime(hours);
                }
                this.updateHeatmap(dataTypeSelect?.value);
            });
        }
    }

    startAutoUpdate() {
        setInterval(() => {
            this.updateHeatmap(document.getElementById('dataType')?.value);
        }, CONFIG.UPDATE_INTERVAL);
    }
}

// 分析控制器
class AnalysisController {
    constructor() {
        this.charts = {};
        this.init();
    }

    init() {
        this.initCharts();
        this.loadAnalysisData();
        this.addResizeListener();
    }

    initCharts() {
        const chartIds = ['spatialAnalysisChart', 'temporalAnalysisChart', 'correlationChart'];
        chartIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                this.charts[id] = echarts.init(el);
            }
        });
    }

    async loadAnalysisData() {
        try {
            const response = await fetch('static/analysis_report.json');
            const data = await response.json();
            this.updateAnalysis(data);
        } catch (error) {
            console.error('Error loading analysis data:', error);
        }
    }

    updateAnalysis(data) {
        this.updateStatistics(data);
        this.updateSpatialAnalysis(data);
        this.updateTemporalAnalysis();
        this.updateCorrelationAnalysis(data);
    }

    updateStatistics(data) {
        const stats = data['总体统计'];
        const elements = {
            dataCount: stats['数据点数量'].toLocaleString(),
            avgEmotion: stats['平均情绪值'].toFixed(2),
            emotionStd: stats['情绪标准差'].toFixed(2)
        };

        Object.entries(elements).forEach(([id, value]) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value;
        });
    }

    updateSpatialAnalysis(data) {
        const spatialData = data['空间分析'];
        const option = {
            title: {
                text: '情绪空间分布',
                left: 'center',
                textStyle: { color: '#fff' }
            },
            tooltip: { trigger: 'axis' },
            xAxis: {
                type: 'category',
                data: Object.keys(spatialData).map(loc => `(${loc})`),
                axisLabel: { rotate: 45 }
            },
            yAxis: {
                type: 'value',
                name: '情绪值'
            },
            series: [{
                name: '平均情绪值',
                type: 'bar',
                data: Object.values(spatialData),
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        {offset: 0, color: '#83bff6'},
                        {offset: 0.5, color: '#188df0'},
                        {offset: 1, color: '#188df0'}
                    ])
                }
            }]
        };

        this.charts.spatialAnalysisChart?.setOption(option);
    }

    updateTemporalAnalysis() {
        const option = {
            title: {
                text: '情绪时间变化',
                left: 'center',
                textStyle: { color: '#fff' }
            },
            tooltip: { trigger: 'axis' },
            xAxis: {
                type: 'time',
                axisLabel: {
                    formatter: '{HH}:00'
                }
            },
            yAxis: {
                type: 'value',
                name: '情绪值'
            },
            series: [{
                name: '平均情绪值',
                type: 'line',
                smooth: true,
                data: this.generateTemporalData(),
                itemStyle: { color: '#6a11cb' },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        {offset: 0, color: 'rgba(106,17,203,0.4)'},
                        {offset: 1, color: 'rgba(106,17,203,0.1)'}
                    ])
                }
            }]
        };

        this.charts.temporalAnalysisChart?.setOption(option);
    }

    updateCorrelationAnalysis(data) {
        const correlations = data['环境相关性'];
        const option = {
            title: {
                text: '环境因素相关性',
                left: 'center',
                textStyle: { color: '#fff' }
            },
            tooltip: { trigger: 'item' },
            radar: {
                indicator: Object.keys(correlations).map(key => ({
                    name: key,
                    max: 1
                }))
            },
            series: [{
                type: 'radar',
                data: [{
                    value: Object.values(correlations),
                    name: '相关系数',
                    itemStyle: { color: '#6a11cb' },
                    areaStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            {offset: 0, color: 'rgba(106,17,203,0.4)'},
                            {offset: 1, color: 'rgba(106,17,203,0.1)'}
                        ])
                    }
                }]
            }]
        };

        this.charts.correlationChart?.setOption(option);
    }

    generateTemporalData() {
        const data = [];
        const now = new Date();
        now.setHours(0, 0, 0, 0);
        
        for (let i = 0; i < 24; i++) {
            data.push([
                new Date(now.getTime() + i * 3600 * 1000),
                utils.generateRandomValue(4, 6)
            ]);
        }
        
        return data;
    }

    addResizeListener() {
        const debouncedResize = utils.debounce(() => {
            Object.values(this.charts).forEach(chart => chart?.resize());
        }, 250);

        window.addEventListener('resize', debouncedResize);
    }
}

// 导航控制器
class NavigationController {
    constructor() {
        this.init();
    }

    init() {
        this.initNavigation();
        this.initScrollEffect();
    }

    initNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        const sections = document.querySelectorAll('.section');
        
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetSection = link.getAttribute('data-section');
                
                navLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');
                
                sections.forEach(section => {
                    section.classList.remove('active');
                    if (section.id === targetSection) {
                        section.classList.add('active');
                    }
                });
            });
        });
        
        document.querySelectorAll('.hero-buttons .cta-button').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const targetSection = button.getAttribute('data-section');
                document.querySelector(`.nav-link[data-section="${targetSection}"]`)?.click();
            });
        });
    }

    initScrollEffect() {
        const nav = document.querySelector('.nav');
        let lastScroll = 0;

        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset;
            
            if (currentScroll <= 0) {
                nav.style.transform = 'translateY(0)';
                return;
            }
            
            if (currentScroll > lastScroll && !nav.classList.contains('scroll-down')) {
                nav.style.transform = 'translateY(-100%)';
                nav.classList.add('scroll-down');
            } else if (currentScroll < lastScroll && nav.classList.contains('scroll-down')) {
                nav.style.transform = 'translateY(0)';
                nav.classList.remove('scroll-down');
            }
            
            lastScroll = currentScroll;
        });
    }
}

// 页面初始化
document.addEventListener('DOMContentLoaded', () => {
    new MapController();
    new AnalysisController();
    new NavigationController();
}); 