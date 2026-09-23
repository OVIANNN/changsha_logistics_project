# -*- coding: utf-8 -*-
"""
长沙物流运行态势分析 —— 阶段 5：五大核心可视化组件
==================================================
本模块定义五个核心可视化组件（均为 Plotly 图），供 Streamlit 仪表盘
（src/dashboard.py）与静态 HTML 报告（outputs/dashboard.html）共用：

  1. 物流运行态势仪表盘        —— 核心指标趋势与同比变化
  2. 多式联运网络地图          —— 中欧班列/货运航线/铁水联运节点空间分布
  3. 快递业务结构堆叠面积图    —— 同城/异地/国际港澳台结构变迁
  4. 区域物流效率热力图        —— 各区县 DEA 效率矩阵热力图
  5. 风险预警看板              —— 异常行为时间序列、阈值线、等级分布
"""

from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BASE_DIR = Path(__file__).resolve().parent.parent
CLEAN_DIR = BASE_DIR / "data" / "cleaned"
OUT_DIR = BASE_DIR / "outputs"

COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]


def load_clean(name: str) -> pd.DataFrame:
    df = pd.read_csv(CLEAN_DIR / name, encoding="utf-8-sig")
    if "月份" in df.columns:
        df["月份"] = pd.to_datetime(df["月份"])
    if "时间" in df.columns:
        df["时间"] = pd.to_datetime(df["时间"])
    return df


def _yoy(series: pd.Series, periods: int = 12) -> pd.Series:
    """同比变化率（%）。"""
    return (series / series.shift(periods) - 1) * 100


# =====================================================================
# 组件 1：物流运行态势仪表盘
# =====================================================================
def component1_operation_dashboard():
    """核心指标趋势与同比变化。返回 (指标卡 DataFrame, 趋势子图 figure)。"""
    express = load_clean("express_monthly.csv").sort_values("月份")
    railway = load_clean("china_railway_monthly.csv").sort_values("月份")
    road = load_clean("road_freight_monthly.csv").sort_values("月份")

    latest = express.iloc[-1]["月份"]
    kpi = pd.DataFrame({
        "指标": ["快递业务量(亿件)", "中欧班列开行量(列)", "公路货运量(万吨)", "快递业务收入(亿元)"],
        "最新值": [
            round(express.iloc[-1]["快递业务量_亿件"], 2),
            int(railway.iloc[-1]["开行列数"]),
            round(road.iloc[-1]["货运量_万吨"], 0),
            round(express.iloc[-1]["业务收入_亿元"], 1),
        ],
        "同比(%)": [
            round(_yoy(express["快递业务量_亿件"]).iloc[-1], 1),
            round(_yoy(railway["开行列数"].astype(float)).iloc[-1], 1),
            round(_yoy(road["货运量_万吨"]).iloc[-1], 1),
            round(_yoy(express["业务收入_亿元"]).iloc[-1], 1),
        ],
    })

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        subplot_titles=("快递业务量", "中欧班列开行量", "公路货运量"),
                        vertical_spacing=0.08)
    fig.add_trace(go.Scatter(x=express["月份"], y=express["快递业务量_亿件"],
                             name="快递业务量", line=dict(color=COLORS[0], width=2)),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=railway["月份"], y=railway["开行列数"],
                             name="中欧班列", line=dict(color=COLORS[1], width=2)),
                  row=2, col=1)
    fig.add_trace(go.Scatter(x=road["月份"], y=road["货运量_万吨"],
                             name="公路货运量", line=dict(color=COLORS[2], width=2)),
                  row=3, col=1)
    fig.update_layout(height=720, title_text="长沙物流核心指标运行态势（2020-2025）",
                      hovermode="x unified", legend=dict(orientation="h"))
    return kpi, fig


# =====================================================================
# 组件 2：多式联运网络地图（Plotly Scattergeo 模拟坐标）
# =====================================================================
def component2_multimodal_map():
    """中欧班列/国际货运航线/铁水联运节点的空间分布与货运流量。"""
    nodes = load_clean("multimodal_nodes.csv")
    routes = load_clean("multimodal_routes.csv")

    fig = go.Figure()

    # 线路（宽度/颜色表示货运量）
    max_vol = routes["货运量_箱"].max()
    type_color = {"中欧班列": "#1f77b4", "国际货运航线": "#2ca02c"}
    for _, r in routes.iterrows():
        fig.add_trace(go.Scattergeo(
            lon=[r["起点经度"], r["终点经度"]],
            lat=[r["起点纬度"], r["终点纬度"]],
            mode="lines",
            line=dict(width=1 + 4 * r["货运量_箱"] / max_vol,
                      color=type_color[r["线路类型"]]),
            name=r["线路名称"],
            opacity=0.6,
            hovertemplate=f"{r['线路名称']}<br>货运量:{r['货运量_箱']}箱<extra></extra>",
        ))

    # 节点（大小表示吞吐量）
    fig.add_trace(go.Scattergeo(
        lon=nodes["经度"], lat=nodes["纬度"],
        mode="markers+text",
        text=nodes["节点名称"],
        textposition="top center",
        marker=dict(size=10 + nodes["年吞吐量_万吨"] / 120,
                    color="#d62728", opacity=0.9,
                    line=dict(width=1, color="white")),
        name="节点",
        hovertemplate="%{text}<br>吞吐量:%{customdata}万吨<extra></extra>",
        customdata=nodes["年吞吐量_万吨"],
    ))

    fig.update_geos(
        projection_type="natural earth",
        showland=True, landcolor="#f2efe9",
        showcountries=True, countrycolor="#cccccc",
        showocean=True, oceancolor="#d9e8f5",
        lataxis_range=[-50, 70], lonaxis_range=[-120, 150],
    )
    fig.update_layout(title_text="长沙多式联运网络（12 条中欧班列精品线路 + 26 条国际货运航线 + 铁水联运节点）",
                      height=560, margin=dict(l=10, r=10, t=60, b=10))
    return fig


# =====================================================================
# 组件 3：快递业务结构堆叠面积图
# =====================================================================
def component3_express_structure():
    """同城/异地/国际港澳台业务量占比的月度变化（堆叠面积）。"""
    express = load_clean("express_monthly.csv").sort_values("月份")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=express["月份"], y=express["同城_亿件"],
                             name="同城", mode="lines", stackgroup="one",
                             line=dict(width=0.5, color=COLORS[1]),
                             fillcolor="rgba(255,127,14,0.6)"))
    fig.add_trace(go.Scatter(x=express["月份"], y=express["异地_亿件"],
                             name="异地", mode="lines", stackgroup="one",
                             line=dict(width=0.5, color=COLORS[0]),
                             fillcolor="rgba(31,119,180,0.6)"))
    fig.add_trace(go.Scatter(x=express["月份"], y=express["国际港澳台_亿件"],
                             name="国际/港澳台", mode="lines", stackgroup="one",
                             line=dict(width=0.5, color=COLORS[2]),
                             fillcolor="rgba(44,160,44,0.6)"))
    fig.update_layout(title_text="长沙快递业务结构堆叠面积图（2020-2025）",
                      xaxis_title="月份", yaxis_title="业务量（亿件）",
                      hovermode="x unified", legend=dict(orientation="h"))
    return fig


# =====================================================================
# 组件 4：区域物流效率热力图（矩阵热力图）
# =====================================================================
def component4_efficiency_heatmap():
    """各区县物流效率矩阵热力图（行：区县，列：年份，颜色：效率值）。
    说明：区县效率值由区县特征（GDP、吞吐量、快递量）确定性合成，
    量级参照阶段 4 DEA 城市效率结果。"""
    districts = load_clean("regional_logistics.csv")
    years = [2020, 2021, 2022, 2023, 2024]

    # 确定性合成效率：经济规模大、快递/园区强度高的区县效率更高
    gdp_norm = (districts["GDP_亿元"] - districts["GDP_亿元"].min()) / \
               (districts["GDP_亿元"].max() - districts["GDP_亿元"].min())
    vol_norm = (districts["快递处理量_万件"] - districts["快递处理量_万件"].min()) / \
               (districts["快递处理量_万件"].max() - districts["快递处理量_万件"].min())
    base_eff = 0.72 + 0.18 * (0.6 * gdp_norm + 0.4 * vol_norm)

    rows = []
    for i, r in districts.iterrows():
        for t, y in enumerate(years):
            eff = base_eff[i] + 0.006 * t + 0.008 * np.sin(i + t)  # 逐年缓升 + 小幅差异
            rows.append({"区县": r["区县"], "年份": y, "效率值": round(float(np.clip(eff, 0.7, 1.0)), 4)})
    eff_df = pd.DataFrame(rows)
    eff_df.to_csv(OUT_DIR / "district_efficiency.csv", index=False, encoding="utf-8-sig")

    pivot = eff_df.pivot(index="区县", columns="年份", values="效率值")
    pivot = pivot.loc[pivot.mean(axis=1).sort_values(ascending=False).index]

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[str(y) for y in pivot.columns],
        y=pivot.index,
        colorscale="RdYlGn", zmin=0.7, zmax=1.0,
        text=np.round(pivot.values, 3),
        texttemplate="%{text}",
        colorbar=dict(title="效率值"),
        hovertemplate="区县:%{y}<br>年份:%{x}<br>效率:%{z:.3f}<extra></extra>",
    ))
    fig.update_layout(title_text="长沙各区县物流效率热力图（DEA 模拟，2020-2024）",
                      xaxis_title="年份", yaxis_title="区县", height=520)
    return fig


# =====================================================================
# 组件 5：风险预警看板
# =====================================================================
def component5_risk_dashboard():
    """货运车辆/船舶异常行为、投诉处罚超阈值可视化预警。返回子图 figure。"""
    risk = load_clean("risk_warnings.csv")
    risk["日期"] = risk["时间"].dt.date

    # 5.1 时间序列异常点（以"货运车辆超速"为例，含阈值线）
    speed = risk[risk["类型"] == "货运车辆超速"].sort_values("时间")
    fig = make_subplots(rows=2, cols=2,
                        subplot_titles=("货运车辆超速时间序列（红线为阈值 90 km/h）",
                                        "超阈值事件按类型分布",
                                        "预警等级分布",
                                        "超阈值事件月度趋势"),
                        specs=[[{"type": "xy"}, {"type": "xy"}],
                               [{"type": "domain"}, {"type": "xy"}]],
                        vertical_spacing=0.16)

    over = speed[speed["是否超阈值"] == 1]
    fig.add_trace(go.Scatter(x=speed["时间"], y=speed["数值"], mode="markers",
                             name="正常/接近", marker=dict(color="#1f77b4", size=5)),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=over["时间"], y=over["数值"], mode="markers",
                             name="超阈值", marker=dict(color="#d62728", size=9, symbol="x")),
                  row=1, col=1)
    fig.add_hline(y=90.0, line_dash="dash", line_color="red", row=1, col=1,
                  annotation_text="阈值 90 km/h")

    # 5.2 超阈值事件按类型分布
    by_type = risk[risk["是否超阈值"] == 1].groupby("类型").size().sort_values(ascending=True)
    fig.add_trace(go.Bar(x=by_type.values, y=by_type.index, orientation="h",
                         name="超阈值次数", marker_color=COLORS[0]),
                  row=1, col=2)

    # 5.3 预警等级饼图
    sev_count = risk["严重程度"].value_counts().reindex(["低", "中", "高", "严重"])
    fig.add_trace(go.Pie(labels=sev_count.index, values=sev_count.values,
                         name="预警等级", hole=0.4,
                         marker=dict(colors=["#2ca02c", "#ff7f0e", "#d62728", "#7f7f7f"])),
                  row=2, col=1)

    # 5.4 超阈值事件月度趋势
    risk["月份"] = risk["时间"].dt.to_period("M").dt.to_timestamp()
    monthly = risk[risk["是否超阈值"] == 1].groupby("月份").size()
    fig.add_trace(go.Scatter(x=monthly.index, y=monthly.values, mode="lines+markers",
                             name="超阈值事件数", line=dict(color="#d62728", width=2)),
                  row=2, col=2)

    fig.update_layout(title_text="长沙物流安全风险预警看板（TOCC 风险识别模块设计）",
                      height=760, showlegend=False)
    return fig


