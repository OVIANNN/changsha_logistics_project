# -*- coding: utf-8 -*-
"""
长沙物流运行态势分析 —— 阶段 3：探索性数据分析（EDA）
====================================================
功能：
  1. 读取清洗后的数据，输出描述性统计；
  2. 绘制月度趋势图（快递、班列、公路货运）；
  3. STL 季节性分解（快递业务量）；
  4. 快递业务结构堆叠面积图；
  5. 中欧班列开行量月度柱状图。
所有图表保存到 outputs/figures/。
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")   # 无界面后端，便于服务器/CI 运行
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from statsmodels.tsa.seasonal import STL

# ---- 全局样式与中文字体 ----
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from plot_config import setup_chinese_font
sns.set_style("whitegrid")
sns.set_palette("Set2")
setup_chinese_font()   # 必须在 seaborn 样式之后调用，避免字体被重置

BASE_DIR = Path(__file__).resolve().parent.parent
CLEAN_DIR = BASE_DIR / "data" / "cleaned"
FIG_DIR = BASE_DIR / "outputs" / "figures"


def save_fig(fig, name: str):
    """保存图表到 outputs/figures/。"""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] 图表已保存：{path}")


def descriptive_statistics():
    """输出各数据表的描述性统计到 CSV。"""
    desc_dir = BASE_DIR / "outputs"
    desc_dir.mkdir(parents=True, exist_ok=True)
    stats = {}
    for f in sorted(CLEAN_DIR.glob("*.csv")):
        if f.name.startswith("_"):
            continue
        df = pd.read_csv(f, encoding="utf-8-sig")
        stats[f.name] = df.describe(include="all").T
    all_stats = pd.concat(stats, names=["数据表", "字段"])
    all_stats.to_csv(desc_dir / "descriptive_statistics.csv", encoding="utf-8-sig")
    print(f"[OK] 描述性统计已保存：outputs/descriptive_statistics.csv")


def monthly_trends():
    """绘制快递业务量、中欧班列、公路货运量的月度趋势图。"""
    express = pd.read_csv(CLEAN_DIR / "express_monthly.csv", encoding="utf-8-sig")
    railway = pd.read_csv(CLEAN_DIR / "china_railway_monthly.csv", encoding="utf-8-sig")
    road = pd.read_csv(CLEAN_DIR / "road_freight_monthly.csv", encoding="utf-8-sig")
    for df in (express, railway, road):
        df["月份"] = pd.to_datetime(df["月份"])

    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    axes[0].plot(express["月份"], express["快递业务量_亿件"], color="#d62728", lw=2)
    axes[0].set_title("长沙月度快递业务量（2020-2025）")
    axes[0].set_ylabel("业务量（亿件）")

    axes[1].plot(railway["月份"], railway["开行列数"], color="#1f77b4", lw=2)
    axes[1].set_title("长沙中欧班列月度开行量（2020-2025）")
    axes[1].set_ylabel("开行列数")

    axes[2].plot(road["月份"], road["货运量_万吨"], color="#2ca02c", lw=2)
    axes[2].set_title("长沙公路货运量（2020-2025）")
    axes[2].set_ylabel("货运量（万吨）")
    axes[2].set_xlabel("月份")

    for ax in axes:
        ax.grid(alpha=0.3)
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    save_fig(fig, "01_monthly_trends.png")


def stl_decomposition():
    """对快递业务量做 STL 季节性分解。"""
    express = pd.read_csv(CLEAN_DIR / "express_monthly.csv", encoding="utf-8-sig")
    express["月份"] = pd.to_datetime(express["月份"])
    series = express.set_index("月份")["快递业务量_亿件"]
    series = series.asfreq("MS")

    stl = STL(series, period=12, robust=True)
    result = stl.fit()

    fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
    result.observed.plot(ax=axes[0], color="black", lw=1.5)
    axes[0].set_title("观测值（Observed）")
    result.trend.plot(ax=axes[1], color="#d62728", lw=1.5)
    axes[1].set_title("趋势（Trend）")
    result.seasonal.plot(ax=axes[2], color="#1f77b4", lw=1.5)
    axes[2].set_title("季节性（Seasonal, 周期=12）")
    result.resid.plot(ax=axes[3], color="#2ca02c", lw=1)
    axes[3].set_title("残差（Residual）")
    for ax in axes:
        ax.grid(alpha=0.3)
        ax.set_ylabel("")
    fig.suptitle("长沙快递业务量 STL 分解", fontsize=14)
    fig.tight_layout()
    save_fig(fig, "02_stl_decomposition.png")

    # 保存分解结果
    decomp = pd.DataFrame({
        "月份": result.observed.index,
        "观测值": result.observed.values,
        "趋势": result.trend.values,
        "季节": result.seasonal.values,
        "残差": result.resid.values,
    })
    decomp.to_csv(BASE_DIR / "outputs" / "stl_decomposition.csv",
                  index=False, encoding="utf-8-sig")
    print("[OK] STL 分解结果已保存：outputs/stl_decomposition.csv")


def express_structure_stacked():
    """快递业务结构堆叠面积图（同城/异地/国际港澳台）。"""
    express = pd.read_csv(CLEAN_DIR / "express_monthly.csv", encoding="utf-8-sig")
    express["月份"] = pd.to_datetime(express["月份"])
    express = express.sort_values("月份")

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.stackplot(express["月份"],
                 express["同城_亿件"], express["异地_亿件"], express["国际港澳台_亿件"],
                 labels=["同城", "异地", "国际/港澳台"],
                 colors=["#ff7f0e", "#1f77b4", "#2ca02c"], alpha=0.85)
    ax.set_title("长沙快递业务结构（2020-2025）")
    ax.set_xlabel("月份")
    ax.set_ylabel("业务量（亿件）")
    ax.legend(loc="upper left")
    ax.grid(alpha=0.3)
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    save_fig(fig, "03_express_structure_stacked.png")


def railway_bar():
    """中欧班列开行量月度柱状图（含出口/进口拆分）。"""
    railway = pd.read_csv(CLEAN_DIR / "china_railway_monthly.csv", encoding="utf-8-sig")
    railway["月份"] = pd.to_datetime(railway["月份"])
    railway = railway.sort_values("月份")

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(railway))
    ax.bar(x, railway["出口列数"], width=0.8, label="出口列数", color="#1f77b4")
    ax.bar(x, railway["进口列数"], width=0.8, bottom=railway["出口列数"],
           label="进口列数", color="#ff7f0e")
    ax.set_xticks(x[::6])
    ax.set_xticklabels(railway["月份"].dt.strftime("%Y-%m")[::6], rotation=45)
    ax.set_title("长沙中欧班列月度开行结构（2020-2025）")
    ax.set_xlabel("月份")
    ax.set_ylabel("列数")
    ax.legend()
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    save_fig(fig, "04_railway_monthly_bar.png")


def main():
    print("=" * 50)
    print("阶段 3：探索性数据分析")
    print("=" * 50)
    descriptive_statistics()
    monthly_trends()
    stl_decomposition()
    express_structure_stacked()
    railway_bar()
    print("\n=== EDA 完成，图表已保存到 outputs/figures/ ===")


if __name__ == "__main__":
    main()

