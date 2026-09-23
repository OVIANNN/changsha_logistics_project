# -*- coding: utf-8 -*-
"""
长沙物流运行态势分析 —— 模拟数据生成器
========================================
说明：
  本脚本基于公开已知的真实统计特征（如 2025 年长沙快递业务量约 28.29 亿件、
  中欧班列开行 1037 列、社会物流总费用与 GDP 比率约 12.8%、长沙黄花机场
  26 条国际货运航线、12 条中欧班列精品线路等），生成符合真实统计规律的
  模拟数据，仅用于方法演示。所有随机过程均使用固定随机种子，保证结果可复现。

生成数据表（共 8 张，保存到 data/ 目录）：
  1. express_monthly.csv          月度快递业务量（2020-2025）
  2. china_railway_monthly.csv    中欧班列月度开行数据（2020-2025）
  3. road_freight_monthly.csv     公路货运量月度数据（2020-2025）
  4. multimodal_nodes.csv         多式联运节点数据
  5. multimodal_routes.csv        多式联运线路数据（用于地图可视化）
  6. regional_logistics.csv       区域（区县）物流数据
  7. dea_panel.csv                物流效率投入产出面板数据（6 城市）
  8. risk_warnings.csv            风险预警模拟数据
"""

import numpy as np
import pandas as pd
from pathlib import Path

# 固定随机种子，保证可复现
RNG = np.random.default_rng(20250923)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# 月份序列：2020-01 ~ 2025-12
MONTHS = pd.date_range("2020-01-01", "2025-12-01", freq="MS")


# =====================================================================
# 1. 月度快递业务量（2020-2025）
# =====================================================================
def gen_express_monthly() -> pd.DataFrame:
    """生成月度快递业务量：总量、同城、异地、国际/港澳台、业务收入。"""
    # 已知真实锚点：2025 年长沙快递业务量约 28.29 亿件
    annual_volume = {2020: 8.20, 2021: 10.80, 2022: 13.50,
                     2023: 16.90, 2024: 22.30, 2025: 28.29}   # 亿件
    # 月度季节性权重（双十一/年末高峰、春节低谷）
    seasonal = {1: 0.075, 2: 0.055, 3: 0.080, 4: 0.078, 5: 0.082, 6: 0.085,
                7: 0.080, 8: 0.082, 9: 0.088, 10: 0.090, 11: 0.115, 12: 0.100}

    rows = []
    for dt in MONTHS:
        year = dt.year
        m = dt.month
        w = seasonal[m] * (1.0 + 0.03 * ((m - 1) / 11.0))   # 年内逐月爬坡
        annual_w_sum = sum(seasonal[mm] * (1.0 + 0.03 * ((mm - 1) / 11.0))
                           for mm in range(1, 13))
        total = annual_volume[year] * w / annual_w_sum
        total *= 1.0 + RNG.normal(0, 0.02)   # 2% 随机扰动

        # 结构占比：同城逐年下降，国际逐年上升
        t = year - 2020
        urban_share = float(np.clip(0.15 - 0.011 * t + RNG.normal(0, 0.003), 0.08, 0.17))
        intl_share = float(np.clip(0.018 + 0.0024 * t + RNG.normal(0, 0.001), 0.015, 0.035))
        intercity_share = 1.0 - urban_share - intl_share

        urban = total * urban_share
        intercity = total * intercity_share
        intl = total * intl_share

        # 业务收入：平均单价逐年下降（10 -> 8.2 元/件）
        price = 10.0 - 0.3 * t + RNG.normal(0, 0.1)
        revenue = total * price  # 亿件 * 元/件 = 亿元

        rows.append({
            "月份": dt.strftime("%Y-%m"),
            "快递业务量_亿件": round(total, 4),
            "同城_亿件": round(urban, 4),
            "异地_亿件": round(intercity, 4),
            "国际港澳台_亿件": round(intl, 4),
            "业务收入_亿元": round(revenue, 2),
        })
    return pd.DataFrame(rows)


# =====================================================================
# 2. 中欧班列月度开行数据（2020-2025）
# =====================================================================
def gen_china_railway_monthly() -> pd.DataFrame:
    """生成中欧班列月度开行数据：开行列数、出口/进口、运量、货值。"""
    # 已知真实锚点：2025 年长沙中欧班列开行 1037 列
    annual_trains = {2020: 320, 2021: 530, 2022: 720,
                     2023: 920, 2024: 1010, 2025: 1037}
    rail_weights = {1: 0.075, 2: 0.060, 3: 0.082, 4: 0.080, 5: 0.085,
                    6: 0.085, 7: 0.085, 8: 0.088, 9: 0.088, 10: 0.092,
                    11: 0.095, 12: 0.085}
    annual_w_sum = sum(rail_weights.values())

    rows = []
    for dt in MONTHS:
        year = dt.year
        m = dt.month
        total = annual_trains[year] * rail_weights[m] / annual_w_sum
        total = max(0, round(total + RNG.normal(0, 2)))
        export = min(round(total * (0.82 + RNG.normal(0, 0.02))), total)
        import_ = total - export
        boxes = round(total * 50 * (1 + RNG.normal(0, 0.03)))   # 每列约 50 箱
        value = total * 2.55e6 * (1 + RNG.normal(0, 0.03))       # 每列货值约 255 万美元

        rows.append({
            "月份": dt.strftime("%Y-%m"),
            "开行列数": total,
            "出口列数": export,
            "进口列数": import_,
            "运量_箱": boxes,
            "货值_美元": round(value, 0),
        })
    return pd.DataFrame(rows)


# =====================================================================
# 3. 公路货运量月度数据（2020-2025）
# =====================================================================
def gen_road_freight_monthly() -> pd.DataFrame:
    """生成公路货运量月度数据：货运量（万吨）、货物周转量（亿吨公里）。"""
    road_weights = {1: 0.078, 2: 0.060, 3: 0.085, 4: 0.082, 5: 0.084,
                    6: 0.084, 7: 0.082, 8: 0.084, 9: 0.086, 10: 0.090,
                    11: 0.095, 12: 0.090}
    annual_w_sum = sum(road_weights.values())

    rows = []
    for dt in MONTHS:
        year = dt.year
        m = dt.month
        annual = 36000 * (1.025 ** (year - 2020))   # 年总量约 3.6 亿吨起步
        volume = annual * road_weights[m] / annual_w_sum
        volume *= 1.0 + RNG.normal(0, 0.015)
        turnover = volume * 180 / 10000   # 平均运距 180 公里 -> 亿吨公里

        rows.append({
            "月份": dt.strftime("%Y-%m"),
            "货运量_万吨": round(volume, 1),
            "货物周转量_亿吨公里": round(turnover, 2),
        })
    return pd.DataFrame(rows)


# =====================================================================
# 4. 多式联运节点数据
# =====================================================================
def gen_multimodal_nodes() -> pd.DataFrame:
    """生成多式联运节点数据：港口/铁路站/机场/园区等。"""
    nodes = [
        ("长沙新港(霞凝港)", "水运", 112.986, 28.352, 2850, 0, "铁水联运核心港区"),
        ("长沙铜官港", "水运", 112.742, 28.545, 1200, 0, "散货/件杂货港区"),
        ("长沙北站(铁路)", "铁路", 113.008, 28.315, 2600, 12, "中欧班列始发站"),
        ("长沙黄花国际机场", "航空", 113.220, 28.190, 95, 26, "国际货运枢纽"),
        ("金霞物流园", "公路", 112.996, 28.330, 1800, 0, "国家级示范物流园区"),
        ("传化公路港(长沙)", "公路", 113.048, 28.232, 950, 0, "公路货运平台"),
        ("长沙霞凝铁路物流园", "铁路", 112.982, 28.345, 1500, 0, "铁路集装箱中心"),
    ]
    df = pd.DataFrame(nodes, columns=["节点名称", "类型", "经度", "纬度",
                                      "年吞吐量_万吨", "线路数", "备注"])
    df["年吞吐量_万吨"] = (df["年吞吐量_万吨"] * (1 + RNG.normal(0, 0.05, len(df)))).round(0)
    return df


# =====================================================================
# 5. 多式联运线路数据（用于地图可视化）
# =====================================================================
def gen_multimodal_routes() -> pd.DataFrame:
    """生成中欧班列精品线路与国际货运航线坐标数据。"""
    # 12 条中欧班列精品线路（长沙 -> 目的地）
    railway_dest = [
        ("莫斯科", 37.617, 55.755), ("明斯克", 27.562, 53.900),
        ("马拉舍维奇(华沙)", 23.155, 52.223), ("汉堡", 9.994, 53.551),
        ("杜伊斯堡", 6.773, 51.435), ("布达佩斯", 19.040, 47.498),
        ("塔什干", 69.240, 41.299), ("阿拉木图", 76.945, 43.238),
        ("德黑兰", 51.389, 35.689), ("河内", 105.834, 21.028),
        ("万象", 102.633, 17.976), ("乌兰巴托", 106.905, 47.886),
    ]
    # 26 条国际货运航线（长沙黄花机场 -> 目的地）
    air_dest = [
        ("法兰克福", 8.682, 50.110), ("阿姆斯特丹", 4.895, 52.371),
        ("列日", 5.570, 50.633), ("布鲁塞尔", 4.352, 50.847),
        ("卢森堡", 6.130, 49.612), ("伦敦", -0.128, 51.507),
        ("米兰", 9.190, 45.464), ("伊斯坦布尔", 28.978, 41.008),
        ("莫斯科(空)", 37.617, 55.755), ("首尔", 126.978, 37.566),
        ("东京", 139.692, 35.689), ("大阪", 135.502, 34.694),
        ("新加坡", 103.820, 1.352), ("曼谷", 100.502, 13.756),
        ("吉隆坡", 101.687, 3.139), ("河内(空)", 105.834, 21.028),
        ("金边", 104.928, 11.556), ("迪拜", 55.271, 25.204),
        ("多哈", 51.531, 25.285), ("悉尼", 151.209, -33.868),
        ("墨尔本", 144.963, -37.814), ("洛杉矶", -118.244, 34.052),
        ("芝加哥", -87.630, 41.878), ("纽约", -74.006, 40.713),
        ("多伦多", -79.383, 43.653), ("圣保罗", -46.633, -23.550),
    ]

    rows = []
    origin_rail = (112.986, 28.352)   # 长沙北站
    origin_air = (113.220, 28.190)    # 长沙黄花机场

    for name, lon, lat in railway_dest:
        rows.append({
            "线路类型": "中欧班列",
            "线路名称": f"长沙-{name}",
            "起点": "长沙", "终点": name,
            "起点经度": origin_rail[0], "起点纬度": origin_rail[1],
            "终点经度": lon, "终点纬度": lat,
            "货运量_箱": int(RNG.integers(800, 3200)),
        })
    for name, lon, lat in air_dest:
        rows.append({
            "线路类型": "国际货运航线",
            "线路名称": f"长沙-{name}",
            "起点": "长沙", "终点": name,
            "起点经度": origin_air[0], "起点纬度": origin_air[1],
            "终点经度": lon, "终点纬度": lat,
            "货运量_箱": int(RNG.integers(400, 5000)),
        })
    return pd.DataFrame(rows)


# =====================================================================
# 6. 区域（区县）物流数据
# =====================================================================
def gen_regional_logistics() -> pd.DataFrame:
    """生成长沙各区县物流数据：快递处理量、园区吞吐量、GDP。"""
    districts = [
        ("长沙县", 98500, 6200, 2250),
        ("浏阳市", 52000, 3800, 1720),
        ("宁乡市", 41000, 3100, 1350),
        ("望城区", 35500, 2800, 1080),
        ("岳麓区", 62000, 4200, 1390),
        ("雨花区", 54000, 3600, 1280),
        ("开福区", 42000, 3300, 850),
        ("芙蓉区", 31000, 2400, 950),
        ("天心区", 28000, 2100, 820),
    ]
    df = pd.DataFrame(districts, columns=["区县", "快递处理量_万件",
                                          "物流园区吞吐量_万吨", "GDP_亿元"])
    df["快递处理量_万件"] = (df["快递处理量_万件"] * (1 + RNG.normal(0, 0.04, len(df)))).round(0)
    df["物流园区吞吐量_万吨"] = (df["物流园区吞吐量_万吨"] * (1 + RNG.normal(0, 0.05, len(df)))).round(0)
    return df


# =====================================================================
# 7. 物流效率投入产出面板数据（6 城市）
# =====================================================================
def gen_dea_panel() -> pd.DataFrame:
    """生成长沙及 5 个对比城市的 DEA 投入产出面板数据。"""
    # 基准值（2020 年）：城市 -> (从业人数_万人, 财政支出_亿元, 等级公路_万公里, GDP_亿元, 进出口_亿元)
    base = {
        "长沙": (18.0, 40.0, 1.90, 12140, 2250),
        "武汉": (25.0, 55.0, 2.10, 15620, 3800),
        "南昌": (10.0, 20.0, 1.40, 5740, 1280),
        "合肥": (14.0, 35.0, 1.70, 10050, 2100),
        "郑州": (20.0, 50.0, 1.80, 12000, 4800),
        "贵阳": (8.0, 15.0, 1.20, 4310, 620),
    }
    # 各指标年增长率
    growth = {
        "长沙": (0.04, 0.06, 0.02, 0.08, 0.06),
        "武汉": (0.03, 0.05, 0.02, 0.08, 0.07),
        "南昌": (0.05, 0.07, 0.03, 0.09, 0.08),
        "合肥": (0.05, 0.08, 0.03, 0.10, 0.10),
        "郑州": (0.04, 0.06, 0.02, 0.08, 0.09),
        "贵阳": (0.06, 0.08, 0.04, 0.10, 0.11),
    }
    rows = []
    for city, b in base.items():
        for t, year in enumerate(range(2020, 2025)):
            g = growth[city]
            labor = b[0] * (1 + g[0]) ** t * (1 + RNG.normal(0, 0.01))
            expense = b[1] * (1 + g[1]) ** t * (1 + RNG.normal(0, 0.01))
            road = b[2] * (1 + g[2]) ** t * (1 + RNG.normal(0, 0.005))
            gdp = b[3] * (1 + g[3]) ** t * (1 + RNG.normal(0, 0.01))
            trade = b[4] * (1 + g[4]) ** t * (1 + RNG.normal(0, 0.02))
            rows.append({
                "城市": city, "年份": year,
                "物流从业人数_万人": round(labor, 2),
                "物流财政支出_亿元": round(expense, 2),
                "等级公路里程_万公里": round(road, 3),
                "GDP_亿元": round(gdp, 0),
                "进出口总额_亿元": round(trade, 0),
            })
    return pd.DataFrame(rows)


# =====================================================================
# 8. 风险预警模拟数据
# =====================================================================
def gen_risk_warnings() -> pd.DataFrame:
    """生成货运车辆/船舶异常行为、投诉处罚超阈值记录。"""
    # (类型, 阈值, 单位)
    risk_types = [
        ("货运车辆超速", 90.0, "km/h"),
        ("货运车辆疲劳驾驶", 4.0, "小时"),
        ("货运车辆偏离路线", 5.0, "km"),
        ("船舶超载", 10.0, "%"),
        ("船舶违规锚泊", 3.0, "次"),
        ("船舶AIS关闭", 2.0, "小时"),
        ("投诉处罚超阈值", 500.0, "万元"),
    ]
    locations = {
        "货运车辆超速": ["京港澳高速长沙段", "长张高速", "绕城高速", "金霞物流园周边"],
        "货运车辆疲劳驾驶": ["长韶娄高速", "京港澳高速", "国道319长沙段"],
        "货运车辆偏离路线": ["长张高速", "绕城高速", "金霞物流园周边"],
        "船舶超载": ["湘江长沙段", "浏阳河航道", "霞凝港水域"],
        "船舶违规锚泊": ["湘江长沙段", "霞凝港水域", "铜官港水域"],
        "船舶AIS关闭": ["湘江长沙段", "浏阳河航道"],
        "投诉处罚超阈值": ["长沙县", "望城区", "岳麓区", "开福区"],
    }

    rows = []
    n = 620
    times = pd.date_range("2024-01-01", "2025-12-31", periods=n)
    for i in range(n):
        t = times[i]
        name, threshold, unit = risk_types[int(RNG.integers(0, len(risk_types)))]
        # 生成数值：约 35% 明显超阈值，其余接近/低于阈值
        if RNG.random() < 0.35:
            value = threshold * RNG.uniform(1.0, 1.8)
        else:
            value = threshold * RNG.uniform(0.3, 1.05)
        is_over = int(value > threshold)

        # 严重程度：按超出比例分级
        ratio = value / threshold
        if ratio > 1.5:
            sev = "严重"
        elif ratio > 1.2:
            sev = "高"
        elif ratio > 1.0:
            sev = "中"
        else:
            sev = "低"

        rows.append({
            "记录ID": f"RK{i+1:04d}",
            "时间": t.strftime("%Y-%m-%d %H:%M"),
            "地点": locations[name][int(RNG.integers(0, len(locations[name])))],
            "类型": name,
            "数值": round(value, 2),
            "阈值": threshold,
            "是否超阈值": is_over,
            "严重程度": sev,
        })
    return pd.DataFrame(rows)


# =====================================================================
# 主流程：生成并保存所有数据表
# =====================================================================
def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    datasets = {
        "express_monthly.csv": gen_express_monthly(),
        "china_railway_monthly.csv": gen_china_railway_monthly(),
        "road_freight_monthly.csv": gen_road_freight_monthly(),
        "multimodal_nodes.csv": gen_multimodal_nodes(),
        "multimodal_routes.csv": gen_multimodal_routes(),
        "regional_logistics.csv": gen_regional_logistics(),
        "dea_panel.csv": gen_dea_panel(),
        "risk_warnings.csv": gen_risk_warnings(),
    }
    for fname, df in datasets.items():
        path = DATA_DIR / fname
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"[OK] 已生成 {path.name}，共 {len(df)} 行")

    print("\n=== 数据生成完成 ===")
    print(f"数据目录：{DATA_DIR}")


if __name__ == "__main__":
    main()
