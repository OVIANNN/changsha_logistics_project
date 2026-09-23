# 长沙物流运行态势分析与降本增效策略研究

基于多源数据的**端到端数据科学项目**，完整走通「数据生成 → 清洗 → 建模 → 可视化 → 报告」闭环，分析长沙物流运行效率、快递业务结构、多式联运通道效能与区域物流空间网络，量化降本增效策略。

> ⚠️ **数据说明**：项目数据为基于公开真实统计特征（2025 年长沙快递业务量约 28.29 亿件、中欧班列开行 1037 列、社会物流总费用与 GDP 比率约 12.8% 等）生成的**模拟数据**，仅用于方法演示。

---

## ✨ 核心亮点

- **🚀 [点击直接打开交互式仪表盘](https://htmlpreview.github.io/?https://github.com/OVIANNN/changsha_logistics_project/blob/main/outputs/dashboard.html)**：无需安装任何环境，浏览器即可查看五大可视化组件（静态 HTML 版，在线渲染）；
- **DEA-Malmquist 物流效率测算**：不依赖 pyDEA，用 scipy 线性规划手写投入导向 CCR 模型；
- **快递业务量预测**：SARIMAX 季节模型 + 95% 置信区间；
- **区域空间网络**：修正引力模型 + NetworkX 中心性与凝聚子群；
- **降本回归**：双对数弹性模型识别「公路占比」为降本第一杠杆；
- **Streamlit 交互式仪表盘**：`streamlit run src/dashboard.py` 启动，支持时间范围筛选等动态交互。

---

## 📊 主要结果预览

| 快递业务量趋势 | DEA 物流效率 | 快递业务量预测 | 区域空间网络 |
|:---:|:---:|:---:|:---:|
| ![趋势](outputs/figures/01_monthly_trends.png) | ![效率](outputs/figures/05_dea_efficiency.png) | ![预测](outputs/figures/07_express_forecast.png) | ![网络](outputs/figures/13_spatial_network.png) |

**核心结论**：

- 快递业务量 2020—2025 年由约 8.2 亿件增至 28.29 亿件，SARIMAX 预测 2026 年延续上升；
- 中欧班列开行量由 329 列增至约 1046 列，货值由 8.46 亿美元增至 26.62 亿美元；
- 长沙物流效率值 1.0（有效前沿面），Malmquist TFP = 1.028；
- 「公路货运占比」弹性系数 +0.485（显著），是降本第一杠杆；
- 铁水联运「每吨降 50 元」测算年节省超 3000 万元。

---

## 🛠 技术栈

| 类别 | 技术 |
|------|------|
| 数据处理 | pandas、numpy |
| 可视化 | matplotlib、seaborn、plotly |
| 统计建模 | statsmodels（STL / SARIMAX / OLS） |
| 优化 | scipy（DEA-CCR 线性规划） |
| 网络分析 | networkx |
| 交互式仪表盘 | streamlit |

---

## 📁 项目结构

```
changsha_logistics_project/
├── data/                      # 原始数据 + 数据字典 + 清洗后数据
│   ├── *.csv                  # 8 张模拟数据表
│   ├── data_dictionary.md     # 数据字典
│   └── cleaned/               # 清洗后数据
├── src/                       # 源代码
│   ├── data_generator.py      # 模拟数据生成
│   ├── 01_data_cleaning.py    # 数据清洗
│   ├── 02_eda.py              # 探索性分析
│   ├── 03_dea_malmquist.py    # DEA-Malmquist 效率测算
│   ├── 04_express_forecast.py # 快递业务量预测
│   ├── 05_multimodal_efficiency.py # 多式联运效能
│   ├── 06_spatial_network.py  # 空间网络分析
│   ├── 07_cost_regression.py  # 成本回归
│   ├── plot_config.py         # 中文字体配置
│   ├── dashboard_components.py# 五大可视化组件
│   ├── dashboard.py           # Streamlit 仪表盘
│   └── generate_static_dashboard.py # 静态 HTML
├── outputs/                   # 图表与中间结果
│   ├── figures/               # 14 张 PNG 图表
│   └── dashboard.html         # 静态仪表盘
├── reports/                   # 报告（Markdown / Word / 博客文章）
├── requirements.txt
└── run_dashboard.bat          # 双击启动仪表盘
```

---

## 🚀 快速开始

```bash
# 1. 克隆并进入项目
git clone <你的仓库地址>
cd changsha_logistics_project

# 2. 安装依赖
pip install -r requirements.txt

# 3. 一键复现全部分析（可选，仓库已含结果）
python src/data_generator.py
python src/01_data_cleaning.py
python src/02_eda.py
python src/03_dea_malmquist.py
python src/04_express_forecast.py
python src/05_multimodal_efficiency.py
python src/06_spatial_network.py
python src/07_cost_regression.py

# 4. 启动交互式仪表盘
streamlit run src/dashboard.py
# 或双击 run_dashboard.bat；静态版直接打开 outputs/dashboard.html
```

---

## 📚 核心分析模块

| 模块 | 文件 | 方法 | 关键结果 |
|------|------|------|---------|
| DEA-Malmquist | `03_dea_malmquist.py` | 手写投入导向 CCR + Malmquist 分解 | 长沙效率 1.0，TFP 1.028 |
| 快递预测 | `04_express_forecast.py` | STL + SARIMAX(1,1,1)(1,1,1,12) | 2026 年 1.98~3.95 亿件/月 |
| 多式联运 | `05_multimodal_efficiency.py` | 成本对比 + 相关性 | 铁水联运年省 3092 万元 |
| 空间网络 | `06_spatial_network.py` | 修正引力模型 + NetworkX | 核心枢纽 + 3 个凝聚子群 |
| 成本回归 | `07_cost_regression.py` | OLS + 双对数弹性 | 公路占比弹性 +0.485 |

**依赖降级说明**：TensorFlow/Torch → SARIMAX；geopandas/folium → Plotly Scattergeo；pyDEA → scipy 自行实现；dash → Streamlit。

---

## 📄 报告

- `reports/final_report.md` — 完整技术报告（含七大章节）
- `reports/长沙物流运行态势分析与降本增效策略研究_呈报版.docx` — 领导呈报版 Word
- `reports/CSDN博客文章.md` — 项目展示博客

---

## 📝 License

本项目仅用于学习与交流，数据为模拟数据，不构成任何实际决策依据。
