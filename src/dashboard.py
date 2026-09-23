# -*- coding: utf-8 -*-
"""
长沙物流运行态势分析与降本增效策略研究 —— 交互式仪表盘（Streamlit）
==================================================================
运行方式（在项目根目录 changsha_logistics_project/ 下执行）：
    streamlit run src/dashboard.py

包含五大核心可视化组件：
  1. 物流运行态势仪表盘
  2. 多式联运网络地图
  3. 快递业务结构堆叠面积图
  4. 区域物流效率热力图
  5. 风险预警看板
"""

import sys
from pathlib import Path
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dashboard_components import (
    component1_operation_dashboard,
    component2_multimodal_map,
    component3_express_structure,
    component4_efficiency_heatmap,
    component5_risk_dashboard,
    load_clean,
)

st.set_page_config(page_title="长沙物流运行态势分析", layout="wide",
                   page_icon="🚚")


@st.cache_data(show_spinner=False)
def cached_component1():
    return component1_operation_dashboard()


def main():
    st.title("🚚 长沙物流运行态势分析与降本增效策略研究")
    st.markdown("> 数据说明：本项目数据为**基于公开真实统计特征的模拟数据**，仅用于方法演示。")

    # ---- 组件 1：物流运行态势仪表盘 ----
    st.header("① 物流运行态势仪表盘")
    kpi, trend_fig = cached_component1()

    # 指标卡（Indicator）
    cols = st.columns(len(kpi))
    for col, (_, row) in zip(cols, kpi.iterrows()):
        delta = row["同比(%)"]
        col.metric(label=row["指标"], value=f"{row['最新值']}",
                   delta=f"{delta}% 同比")

    # 时间范围选择
    express = load_clean("express_monthly.csv").sort_values("月份")
    min_date, max_date = express["月份"].min().to_pydatetime(), express["月份"].max().to_pydatetime()
    date_range = st.slider("选择时间范围", min_value=min_date, max_value=max_date,
                           value=(min_date, max_date), format="YYYY-MM")
    # 根据选择过滤趋势图
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go
    railway = load_clean("china_railway_monthly.csv").sort_values("月份")
    road = load_clean("road_freight_monthly.csv").sort_values("月份")
    e2 = express[(express["月份"] >= date_range[0]) & (express["月份"] <= date_range[1])]
    r2 = railway[(railway["月份"] >= date_range[0]) & (railway["月份"] <= date_range[1])]
    rd2 = road[(road["月份"] >= date_range[0]) & (road["月份"] <= date_range[1])]

    filtered_fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                                 subplot_titles=("快递业务量", "中欧班列开行量", "公路货运量"))
    filtered_fig.add_trace(go.Scatter(x=e2["月份"], y=e2["快递业务量_亿件"], line=dict(width=2)), row=1, col=1)
    filtered_fig.add_trace(go.Scatter(x=r2["月份"], y=r2["开行列数"], line=dict(width=2)), row=2, col=1)
    filtered_fig.add_trace(go.Scatter(x=rd2["月份"], y=rd2["货运量_万吨"], line=dict(width=2)), row=3, col=1)
    filtered_fig.update_layout(height=650, title_text="核心指标趋势（时间范围筛选）",
                               hovermode="x unified")
    st.plotly_chart(filtered_fig, width="stretch")

    # ---- 组件 2：多式联运网络地图 ----
    st.header("② 多式联运网络地图")
    st.plotly_chart(component2_multimodal_map(), width="stretch")

    # ---- 组件 3：快递业务结构堆叠面积图 ----
    st.header("③ 快递业务结构堆叠面积图")
    st.plotly_chart(component3_express_structure(), width="stretch")

    # ---- 组件 4：区域物流效率热力图 ----
    st.header("④ 区域物流效率热力图")
    st.plotly_chart(component4_efficiency_heatmap(), width="stretch")

    # ---- 组件 5：风险预警看板 ----
    st.header("⑤ 风险预警看板")
    st.plotly_chart(component5_risk_dashboard(), width="stretch")


if __name__ == "__main__":
    main()
