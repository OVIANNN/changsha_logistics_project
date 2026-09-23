# -*- coding: utf-8 -*-
"""
长沙物流运行态势分析 —— 阶段 3：数据清洗
========================================
功能：
  1. 读取 data/ 目录下的所有原始 CSV；
  2. 处理缺失值（时间序列用前向/插值填充，其余按列均值/众数填充）；
  3. 处理异常值（基于 3σ / IQR 的 Winsorize 截尾）；
  4. 统一时间格式（"月份" -> 标准月度周期）；
  5. 输出清洗后的数据到 data/cleaned/。
"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data"
CLEAN_DIR = BASE_DIR / "data" / "cleaned"

# 时间序列类数据表（含"月份"字段）
TS_FILES = ["express_monthly.csv", "china_railway_monthly.csv", "road_freight_monthly.csv"]


def load_raw(filename: str) -> pd.DataFrame:
    """读取原始 CSV，统一时间列格式。"""
    df = pd.read_csv(RAW_DIR / filename, encoding="utf-8-sig")
    if "月份" in df.columns:
        df["月份"] = pd.to_datetime(df["月份"], format="%Y-%m")
    if "时间" in df.columns:
        df["时间"] = pd.to_datetime(df["时间"], format="%Y-%m-%d %H:%M")
    return df


def handle_missing(df: pd.DataFrame) -> tuple:
    """处理缺失值，返回 (处理后 df, 缺失统计)。"""
    missing_before = int(df.isna().sum().sum())
    # 数值列：用列中位数填充
    num_cols = df.select_dtypes(include=[np.number]).columns
    for c in num_cols:
        if df[c].isna().any():
            df[c] = df[c].fillna(df[c].median())
    # 分类/文本列：用众数填充
    obj_cols = df.select_dtypes(exclude=["number", "datetime64", "bool"]).columns
    for c in obj_cols:
        if df[c].isna().any():
            df[c] = df[c].fillna(df[c].mode()[0] if not df[c].mode().empty else "未知")
    return df, missing_before


def winsorize_outliers(df: pd.DataFrame) -> tuple:
    """基于 IQR 对数值列做 Winsorize 截尾，返回 (处理后 df, 截尾数量)。"""
    n_outliers = 0
    num_cols = df.select_dtypes(include=[np.number]).columns
    for c in num_cols:
        q1, q3 = df[c].quantile(0.25), df[c].quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = (df[c] < lower) | (df[c] > upper)
        n_outliers += int(mask.sum())
        df[c] = df[c].clip(lower, upper)
    return df, n_outliers


def main():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    summary = []

    for filename in sorted(RAW_DIR.glob("*.csv")):
        df = load_raw(filename.name)

        # 时间序列数据：按月份排序
        if filename.name in TS_FILES:
            df = df.sort_values("月份").reset_index(drop=True)

        df, missing_before = handle_missing(df)
        df, n_out = winsorize_outliers(df)

        df.to_csv(CLEAN_DIR / filename.name, index=False, encoding="utf-8-sig")
        summary.append({
            "文件": filename.name,
            "行数": len(df),
            "列数": df.shape[1],
            "填充缺失值": missing_before,
            "截尾异常值": n_out,
        })
        print(f"[OK] 清洗 {filename.name}: {len(df)} 行, "
              f"填充缺失 {missing_before}, 截尾异常 {n_out}")

    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(CLEAN_DIR / "_cleaning_summary.csv", index=False, encoding="utf-8-sig")
    print("\n=== 数据清洗完成 ===")
    print(f"清洗后数据目录：{CLEAN_DIR}")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
