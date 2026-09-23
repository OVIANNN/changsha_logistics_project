# -*- coding: utf-8 -*-
"""
长沙物流运行态势分析 —— 阶段 4.5：物流成本影响因素回归分析
==========================================================
方法：
  1. 构造模拟面板数据（6 城市 × 6 年），被解释变量为"社会物流总费用与 GDP 比率"，
     解释变量为运输结构（公路货运占比）、枢纽能级、信息化水平、政策支持；
  2. 使用 OLS 回归（statsmodels）估计各因素影响，并输出回归摘要与弹性系数
     （通过双对数模型 ln(y) ~ ln(X) 得到弹性）；
  3. 基于结果提出降本增效策略建议。

说明：面板数据为模拟数据，用于方法演示；弹性系数符号与量级参照物流经济常识设定。
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plot_config import setup_chinese_font
setup_chinese_font()

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "outputs"
FIG_DIR = OUT_DIR / "figures"

RNG = np.random.default_rng(20250923)

FEATURES = ["公路货运占比", "枢纽能级指数", "信息化水平指数", "政策支持指数"]


def simulate_panel() -> pd.DataFrame:
    """生成物流成本影响因素的模拟面板数据。"""
    cities = ["长沙", "武汉", "南昌", "合肥", "郑州", "贵阳"]
    years = list(range(2020, 2026))
    # 各城市基准水平（体现区域差异）
    city_base = {
        "长沙": (0.72, 78, 75, 80),
        "武汉": (0.70, 82, 78, 78),
        "南昌": (0.80, 62, 58, 60),
        "合肥": (0.74, 72, 70, 72),
        "郑州": (0.71, 80, 74, 76),
        "贵阳": (0.85, 55, 50, 52),
    }
    rows = []
    for city in cities:
        b_road, b_hub, b_info, b_policy = city_base[city]
        for year in years:
            t = year - 2020
            road = np.clip(b_road - 0.01 * t + RNG.normal(0, 0.01), 0.5, 0.9)
            hub = np.clip(b_hub + 2.0 * t + RNG.normal(0, 1.5), 30, 100)
            info = np.clip(b_info + 3.0 * t + RNG.normal(0, 1.5), 30, 100)
            policy = np.clip(b_policy + 2.0 * t + RNG.normal(0, 1.5), 30, 100)
            # 真实关系：公路占比↑→成本占比↑；枢纽/信息化/政策↑→成本占比↓
            cost_ratio = (20.0 + 8.0 * road - 0.03 * hub - 0.03 * info
                          - 0.02 * policy + RNG.normal(0, 0.25))
            rows.append({
                "城市": city, "年份": year,
                "物流成本占GDP比率": round(cost_ratio, 3),
                "公路货运占比": round(road, 3),
                "枢纽能级指数": round(hub, 1),
                "信息化水平指数": round(info, 1),
                "政策支持指数": round(policy, 1),
            })
    return pd.DataFrame(rows)


def run_regression(panel: pd.DataFrame):
    """运行线性 OLS 与双对数（弹性）回归。"""
    # ---- 线性回归 ----
    X = panel[FEATURES]
    X = sm.add_constant(X)
    y = panel["物流成本占GDP比率"]
    linear = sm.OLS(y, X).fit()

    # ---- 双对数回归（弹性） ----
    X_log = np.log(panel[FEATURES])
    X_log = sm.add_constant(X_log)
    y_log = np.log(panel["物流成本占GDP比率"])
    loglog = sm.OLS(y_log, X_log).fit()

    # 弹性系数
    elasticity = pd.DataFrame({
        "变量": ["常数项"] + FEATURES,
        "弹性系数": loglog.params.round(4).values,
        "p值": loglog.pvalues.round(4).values,
    })
    elasticity.to_csv(OUT_DIR / "elasticity_coefficients.csv",
                      index=False, encoding="utf-8-sig")

    # 线性回归结果表
    linear_table = pd.DataFrame({
        "变量": ["常数项"] + FEATURES,
        "系数": linear.params.round(4).values,
        "标准误": linear.bse.round(4).values,
        "t值": linear.tvalues.round(3).values,
        "p值": linear.pvalues.round(4).values,
    })
    linear_table.to_csv(OUT_DIR / "regression_results.csv",
                        index=False, encoding="utf-8-sig")

    # 回归摘要文本
    with open(OUT_DIR / "regression_summary.txt", "w", encoding="utf-8") as f:
        f.write("===== 线性回归（OLS） =====\n")
        f.write(linear.summary().as_text())
        f.write("\n\n===== 双对数回归（弹性） =====\n")
        f.write(loglog.summary().as_text())

    # ---- 弹性系数图 ----
    coefs = loglog.params[FEATURES]
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = ["#d62728" if c > 0 else "#2ca02c" for c in coefs]
    ax.barh(FEATURES[::-1], coefs.values[::-1], color=colors[::-1])
    ax.axvline(0, color="gray", lw=1)
    ax.set_title("物流成本弹性系数（双对数模型）")
    ax.set_xlabel("弹性系数")
    for i, v in enumerate(coefs.values[::-1]):
        ax.text(v + (0.01 if v >= 0 else -0.01), i, f"{v:.3f}",
                va="center", ha="left" if v >= 0 else "right")
    ax.grid(alpha=0.3, axis="x")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "14_cost_elasticity.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    return linear, loglog, elasticity


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    panel = simulate_panel()
    panel.to_csv(OUT_DIR / "cost_panel.csv", index=False, encoding="utf-8-sig")

    linear, loglog, elasticity = run_regression(panel)

    print("=== 物流成本回归分析完成 ===")
    print(f"线性模型 R2 = {linear.rsquared:.4f}；双对数模型 R2 = {loglog.rsquared:.4f}")
    print("\n弹性系数：")
    print(elasticity.to_string(index=False))
    print("\n策略建议：")
    print("  - 公路货运占比每降低 1%，物流成本占比下降约 "
          f"{abs(elasticity.loc[1,'弹性系数']):.3f}%")
    print("  - 提升多式联运、枢纽能级、信息化与政策支持是降本关键路径。")


if __name__ == "__main__":
    main()
