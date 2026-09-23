# -*- coding: utf-8 -*-
"""
长沙物流运行态势分析 —— 生成静态 HTML 仪表盘
===========================================
将五大核心可视化组件组合为单个自包含 HTML 文件 outputs/dashboard.html，
便于在浏览器中直接打开（无需启动 Streamlit 服务）。

生成方式：python src/generate_static_dashboard.py
打开方式：双击 outputs/dashboard.html 或浏览器打开该文件。
"""

import sys
from pathlib import Path
import plotly.io as pio

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dashboard_components import (
    component1_operation_dashboard,
    component2_multimodal_map,
    component3_express_structure,
    component4_efficiency_heatmap,
    component5_risk_dashboard,
)

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "outputs"

SECTIONS = [
    ("① 物流运行态势仪表盘", "核心指标趋势与同比变化"),
    ("② 多式联运网络地图", "12 条中欧班列精品线路 + 26 条国际货运航线 + 铁水联运节点"),
    ("③ 快递业务结构堆叠面积图", "同城/异地/国际港澳台结构变迁"),
    ("④ 区域物流效率热力图", "各区县 DEA 效率矩阵"),
    ("⑤ 风险预警看板", "异常行为时间序列、阈值线、预警等级分布"),
]


def kpi_html(kpi) -> str:
    """生成指标卡 HTML 表格。"""
    cards = "".join(
        f'<div class="kpi"><div class="kpi-label">{r["指标"]}</div>'
        f'<div class="kpi-value">{r["最新值"]}</div>'
        f'<div class="kpi-delta" style="color:{("#d62728" if r["同比(%)"] >= 0 else "#2ca02c")};">'
        f'同比 {r["同比(%)"]:+.1f}%</div></div>'
        for _, r in kpi.iterrows()
    )
    return f'<div class="kpi-row">{cards}</div>'


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    kpi, op_fig = component1_operation_dashboard()
    figs = [
        op_fig,
        component2_multimodal_map(),
        component3_express_structure(),
        component4_efficiency_heatmap(),
        component5_risk_dashboard(),
    ]

    body = ["<h1>🚚 长沙物流运行态势分析与降本增效策略研究</h1>",
            "<p class='note'>数据说明：本项目数据为<strong>基于公开真实统计特征的模拟数据</strong>，仅用于方法演示。</p>"]
    body.append(kpi_html(kpi))
    for (title, desc), fig in zip(SECTIONS, figs):
        body.append(f"<h2>{title}</h2><p class='desc'>{desc}</p>")
        body.append(pio.to_html(fig, full_html=False, include_plotlyjs="cdn"))

    css = """
    <style>
      body { font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif; margin: 20px 40px; background:#f7f8fa; }
      h1 { color:#1f3864; }
      h2 { color:#2e5a88; border-bottom:2px solid #2e5a88; padding-bottom:6px; margin-top:40px; }
      .note { color:#777; }
      .desc { color:#555; margin-top:-10px; }
      .kpi-row { display:flex; gap:16px; flex-wrap:wrap; margin:20px 0; }
      .kpi { flex:1; min-width:180px; background:#fff; border-radius:10px; padding:16px;
             box-shadow:0 2px 6px rgba(0,0,0,0.08); }
      .kpi-label { color:#888; font-size:14px; }
      .kpi-value { font-size:28px; font-weight:bold; color:#1f3864; }
      .kpi-delta { font-size:14px; margin-top:4px; }
    </style>
    """

    html = ("<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'>"
            "<title>长沙物流运行态势分析仪表盘</title>" + css + "</head><body>"
            + "\n".join(body) + "</body></html>")

    out = OUT_DIR / "dashboard.html"
    out.write_text(html, encoding="utf-8")
    print(f"[OK] 静态仪表盘已生成：{out}")


if __name__ == "__main__":
    main()
