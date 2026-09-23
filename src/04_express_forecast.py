# -*- coding: utf-8 -*-
"""
长沙物流运行态势分析 —— 阶段 4.2：快递业务量预测
================================================
方法：
  1. 对快递业务总量做 STL 时序分解，分析趋势、季节与残差；
  2. 使用 SARIMAX（季节差分 + 自回归/移动平均）预测未来 12 个月业务量，
     若 SARIMAX 拟合失败则回退到"趋势外推 + 季节因子"方法；
  3. 对比同城、异地、国际/港澳台业务量变化趋势；
  4. 输出预测结果 CSV 与预测图。

说明：由于 TensorFlow/Torch 不可用，本模块采用 statsmodels 的 SARIMAX 作为时间序列模型。
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import STL

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plot_config import setup_chinese_font
setup_chinese_font()

BASE_DIR = Path(__file__).resolve().parent.parent
CLEAN_DIR = BASE_DIR / "data" / "cleaned"
OUT_DIR = BASE_DIR / "outputs"
FIG_DIR = OUT_DIR / "figures"

FORECAST_STEPS = 12   # 预测未来 12 个月


def load_series() -> pd.Series:
    df = pd.read_csv(CLEAN_DIR / "express_monthly.csv", encoding="utf-8-sig")
    df["月份"] = pd.to_datetime(df["月份"])
    df = df.sort_values("月份")
    return df.set_index("月份")["快递业务量_亿件"].asfreq("MS")


def fallback_forecast(series: pd.Series, steps: int):
    """回退方法：线性趋势外推 + 月度季节因子。"""
    t = np.arange(len(series))
    coef = np.polyfit(t, series.values, 1)
    trend = coef[0] * t + coef[1]
    seasonal = np.array([series.values[i] - trend[i] for i in range(len(series))])
    month_seasonal = np.array([seasonal[np.arange(i, len(seasonal), 12)].mean()
                               for i in range(12)])
    future = np.arange(len(series), len(series) + steps)
    fc = coef[0] * future + coef[1] + month_seasonal[future % 12]
    fc = np.maximum(fc, 0)
    idx = pd.date_range(series.index[-1] + pd.offsets.MonthBegin(1), periods=steps, freq="MS")
    return pd.Series(fc, index=idx), None, None


def sarimax_forecast(series: pd.Series, steps: int):
    """SARIMAX 预测，返回 (预测序列, 置信区间 DataFrame, 模型)。"""
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    model = SARIMAX(series, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12),
                    trend="c", enforce_stationarity=False, enforce_invertibility=False)
    fit = model.fit(disp=False, maxiter=200)
    fc = fit.get_forecast(steps)
    mean = fc.predicted_mean
    ci = fc.conf_int(alpha=0.05)
    return mean, ci, fit


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    series = load_series()

    # 1) STL 分解（保存）
    stl = STL(series, period=12, robust=True).fit()
    decomp = pd.DataFrame({
        "月份": series.index,
        "观测值": series.values,
        "趋势": stl.trend.values,
        "季节": stl.seasonal.values,
        "残差": stl.resid.values,
    })
    decomp.to_csv(OUT_DIR / "express_stl.csv", index=False, encoding="utf-8-sig")

    # 2) 预测
    try:
        fc_mean, fc_ci, model = sarimax_forecast(series, FORECAST_STEPS)
        method = "SARIMAX(1,1,1)(1,1,1,12)"
    except Exception as e:
        print(f"[警告] SARIMAX 拟合失败（{e}），回退到趋势+季节因子法。")
        fc_mean, fc_ci, model = fallback_forecast(series, FORECAST_STEPS)
        method = "趋势外推+季节因子(回退)"

    forecast_df = pd.DataFrame({
        "月份": fc_mean.index.strftime("%Y-%m"),
        "预测业务量_亿件": fc_mean.values.round(4),
    })
    if fc_ci is not None:
        forecast_df["置信下限_95%"] = fc_ci.iloc[:, 0].values.round(4)
        forecast_df["置信上限_95%"] = fc_ci.iloc[:, 1].values.round(4)
    forecast_df.to_csv(OUT_DIR / "express_forecast.csv", index=False, encoding="utf-8-sig")

    # 3) 预测图
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(series.index, series.values, color="#1f77b4", lw=2, label="历史业务量")
    ax.plot(fc_mean.index, fc_mean.values, color="#d62728", lw=2, marker="o", label="预测业务量")
    if fc_ci is not None:
        ax.fill_between(fc_mean.index, fc_ci.iloc[:, 0], fc_ci.iloc[:, 1],
                        color="#d62728", alpha=0.2, label="95% 置信区间")
    ax.axvline(series.index[-1], color="gray", ls="--", lw=1)
    ax.set_title(f"长沙快递业务量预测（{method}）")
    ax.set_xlabel("月份")
    ax.set_ylabel("业务量（亿件）")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "07_express_forecast.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # 4) 同城/异地/国际 趋势对比
    df = pd.read_csv(CLEAN_DIR / "express_monthly.csv", encoding="utf-8-sig")
    df["月份"] = pd.to_datetime(df["月份"])
    df = df.sort_values("月份")
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df["月份"], df["异地_亿件"], label="异地", color="#1f77b4", lw=2)
    ax.plot(df["月份"], df["同城_亿件"], label="同城", color="#ff7f0e", lw=2)
    ax.plot(df["月份"], df["国际港澳台_亿件"], label="国际/港澳台", color="#2ca02c", lw=2)
    ax.set_title("长沙快递业务结构趋势对比（同城/异地/国际港澳台）")
    ax.set_xlabel("月份")
    ax.set_ylabel("业务量（亿件）")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "08_express_type_trends.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"=== 快递业务量预测完成（方法：{method}）===")
    print("未来 12 个月预测：")
    print(forecast_df.to_string(index=False))


if __name__ == "__main__":
    main()
