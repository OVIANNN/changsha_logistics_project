# -*- coding: utf-8 -*-
"""
长沙物流运行态势分析 —— 阶段 4.1：DEA-Malmquist 物流效率测算
============================================================
方法：
  1. 使用数据包络分析（DEA）投入导向 CCR 模型测算长沙及 5 个对比城市的物流效率。
     投入指标：物流从业人数、物流财政支出、等级公路里程；
     产出指标：GDP、商品进出口总额。
  2. 基于面板数据计算 Malmquist 全要素生产率指数，并分解为：
       技术效率变化（TEC，追赶效应）与技术变化（TC，前沿移动）。
  3. 输出效率排名表与 Malmquist 指数表（CSV + 图表）。

说明：本模块自行实现 DEA-CCR（线性规划，scipy.optimize.linprog），不依赖 pyDEA。
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import linprog

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plot_config import setup_chinese_font
setup_chinese_font()

BASE_DIR = Path(__file__).resolve().parent.parent
CLEAN_DIR = BASE_DIR / "data" / "cleaned"
OUT_DIR = BASE_DIR / "outputs"
FIG_DIR = OUT_DIR / "figures"

INPUT_COLS = ["物流从业人数_万人", "物流财政支出_亿元", "等级公路里程_万公里"]
OUTPUT_COLS = ["GDP_亿元", "进出口总额_亿元"]


def dea_ccr(X_ref: np.ndarray, Y_ref: np.ndarray,
            x0: np.ndarray, y0: np.ndarray) -> float:
    """投入导向 CCR 模型，返回决策单元 (x0, y0) 相对前沿面的效率值 theta。"""
    n, m = X_ref.shape
    s = Y_ref.shape[1]
    c = np.zeros(n + 1)
    c[0] = 1.0

    A_ub = np.zeros((m + s, n + 1))
    b_ub = np.zeros(m + s)
    for i in range(m):               # 投入约束：-theta*x0 + X*lambda <= 0
        A_ub[i, 0] = -x0[i]
        A_ub[i, 1:] = X_ref[:, i]
        b_ub[i] = 0.0
    for r in range(s):               # 产出约束：-Y*lambda <= -y0
        A_ub[m + r, 1:] = -Y_ref[:, r]
        b_ub[m + r] = -y0[r]

    bounds = [(0.0, None)] * (n + 1)
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
    return float(res.x[0]) if res.success else np.nan


def compute_efficiency(panel: pd.DataFrame) -> pd.DataFrame:
    """逐年计算每个城市的 CCR 效率值。"""
    records = []
    for year, grp in panel.groupby("年份"):
        X = grp[INPUT_COLS].to_numpy(dtype=float)
        Y = grp[OUTPUT_COLS].to_numpy(dtype=float)
        for _, row in grp.iterrows():
            theta = dea_ccr(X, Y, row[INPUT_COLS].to_numpy(dtype=float),
                            row[OUTPUT_COLS].to_numpy(dtype=float))
            records.append({"城市": row["城市"], "年份": year, "效率值": round(theta, 4)})
    return pd.DataFrame(records)


def compute_malmquist(panel: pd.DataFrame) -> pd.DataFrame:
    """计算 Malmquist 指数及其分解（逐城市、逐相邻年份）。"""
    years = sorted(panel["年份"].unique())
    cities = sorted(panel["城市"].unique())

    frontiers = {}
    for y in years:
        g = panel[panel["年份"] == y].sort_values("城市")
        frontiers[y] = {
            "X": g[INPUT_COLS].to_numpy(dtype=float),
            "Y": g[OUTPUT_COLS].to_numpy(dtype=float),
            "city_idx": {c: i for i, c in enumerate(g["城市"])},
        }

    records = []
    for city in cities:
        for t in range(len(years) - 1):
            yt, yt1 = years[t], years[t + 1]
            ft, ft1 = frontiers[yt], frontiers[yt1]
            i, j = ft["city_idx"][city], ft1["city_idx"][city]

            x_t, y_t = ft["X"][i], ft["Y"][i]
            x_t1, y_t1 = ft1["X"][j], ft1["Y"][j]

            d_tt = dea_ccr(ft["X"], ft["Y"], x_t, y_t)
            d_tt1 = dea_ccr(ft["X"], ft["Y"], x_t1, y_t1)
            d_t1t = dea_ccr(ft1["X"], ft1["Y"], x_t, y_t)
            d_t1t1 = dea_ccr(ft1["X"], ft1["Y"], x_t1, y_t1)

            tec = d_t1t1 / d_tt if d_tt else np.nan
            tc = np.sqrt((d_tt / d_t1t) * (d_tt1 / d_t1t1)) if (d_t1t and d_t1t1) else np.nan
            mi = tec * tc

            records.append({
                "城市": city, "时期": f"{yt}-{yt1}",
                "技术效率变化_TEC": round(tec, 4),
                "技术变化_TC": round(tc, 4),
                "Malmquist_TFP": round(mi, 4),
            })
    return pd.DataFrame(records)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    panel = pd.read_csv(CLEAN_DIR / "dea_panel.csv", encoding="utf-8-sig")

    eff = compute_efficiency(panel)
    eff.to_csv(OUT_DIR / "dea_efficiency.csv", index=False, encoding="utf-8-sig")

    mi = compute_malmquist(panel)
    mi.to_csv(OUT_DIR / "malmquist_index.csv", index=False, encoding="utf-8-sig")

    # 各城市平均 Malmquist 指数（几何均值）
    mi_mean = mi.groupby("城市")[["技术效率变化_TEC", "技术变化_TC", "Malmquist_TFP"]].apply(
        lambda g: g.prod() ** (1 / len(g))).round(4).reset_index()
    mi_mean.to_csv(OUT_DIR / "malmquist_summary.csv", index=False, encoding="utf-8-sig")

    # 图表 1：各城市逐年效率值
    fig, ax = plt.subplots(figsize=(10, 6))
    for city in eff["城市"].unique():
        sub = eff[eff["城市"] == city]
        ax.plot(sub["年份"], sub["效率值"], marker="o", label=city)
    ax.axhline(1.0, color="gray", ls="--", lw=1)
    ax.set_title("六城市物流效率（DEA-CCR 投入导向，2020-2024）")
    ax.set_xlabel("年份")
    ax.set_ylabel("效率值")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "05_dea_efficiency.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # 图表 2：平均 Malmquist 指数及分解
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(mi_mean))
    w = 0.28
    ax.bar(x - w, mi_mean["技术效率变化_TEC"], w, label="技术效率变化(TEC)", color="#1f77b4")
    ax.bar(x, mi_mean["技术变化_TC"], w, label="技术变化(TC)", color="#ff7f0e")
    ax.bar(x + w, mi_mean["Malmquist_TFP"], w, label="Malmquist TFP", color="#2ca02c")
    ax.axhline(1.0, color="gray", ls="--", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels(mi_mean["城市"])
    ax.set_title("各城市平均 Malmquist 指数及分解（2020-2024 几何均值）")
    ax.set_ylabel("指数值（>1 表示改善）")
    ax.legend()
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "06_malmquist_index.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # 输出排名表
    rank = eff[eff["年份"] == 2024].sort_values("效率值", ascending=False).reset_index(drop=True)
    rank["排名"] = rank.index + 1
    rank.to_csv(OUT_DIR / "dea_ranking_2024.csv", index=False, encoding="utf-8-sig")

    print("=== DEA-Malmquist 完成 ===")
    print("2024 年效率排名：")
    print(rank.to_string(index=False))
    print("\n各城市平均 Malmquist 指数：")
    print(mi_mean.to_string(index=False))


if __name__ == "__main__":
    main()

