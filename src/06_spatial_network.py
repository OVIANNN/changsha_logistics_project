# -*- coding: utf-8 -*-
"""
长沙物流运行态势分析 —— 阶段 4.4：区域物流空间网络分析
======================================================
方法：
  1. 使用修正引力模型计算长沙各区县及周边城市的物流联系强度：
        F_ij = G_i * G_j / d_ij^γ  （G 为经济质量，d 为球面距离，γ 为距离衰减系数）
  2. 使用 NetworkX 构建加权网络，计算度中心性、介数中心性、凝聚子群；
  3. 绘制网络图，识别核心枢纽与辐射范围；
  4. 输出网络指标 CSV 与网络可视化图。
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from networkx.algorithms import community

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plot_config import setup_chinese_font
setup_chinese_font()

BASE_DIR = Path(__file__).resolve().parent.parent
CLEAN_DIR = BASE_DIR / "data" / "cleaned"
OUT_DIR = BASE_DIR / "outputs"
FIG_DIR = OUT_DIR / "figures"

GAMMA = 1.5            # 距离衰减系数
THRESHOLD_PCT = 0.35   # 仅保留联系强度前 35% 的边


def haversine(lon1, lat1, lon2, lat2):
    """球面距离（公里）。"""
    R = 6371.0
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def build_nodes() -> pd.DataFrame:
    """构建节点表（区县 + 周边城市），含经纬度与 GDP（经济质量）。"""
    districts = pd.read_csv(CLEAN_DIR / "regional_logistics.csv", encoding="utf-8-sig")
    district_coords = {
        "长沙县": (113.08, 28.25), "浏阳市": (113.63, 28.16),
        "宁乡市": (112.55, 28.28), "望城区": (112.82, 28.36),
        "岳麓区": (112.93, 28.23), "雨花区": (113.03, 28.13),
        "开福区": (112.98, 28.23), "芙蓉区": (113.03, 28.19),
        "天心区": (112.99, 28.11),
    }
    nodes = []
    for _, r in districts.iterrows():
        lon, lat = district_coords[r["区县"]]
        nodes.append({"名称": r["区县"], "类型": "区县",
                      "经度": lon, "纬度": lat, "GDP_亿元": r["GDP_亿元"]})
    cities = [
        ("岳阳", 113.13, 29.36, 4700), ("株洲", 113.13, 27.83, 3900),
        ("湘潭", 112.94, 27.83, 2800), ("衡阳", 112.57, 26.90, 4300),
        ("常德", 111.70, 29.03, 4400), ("益阳", 112.36, 28.55, 2100),
        ("娄底", 112.00, 27.70, 2000), ("武汉", 114.30, 30.59, 21000),
        ("南昌", 115.86, 28.68, 7800), ("合肥", 117.28, 31.86, 13500),
        ("郑州", 113.63, 34.75, 14500),
    ]
    for name, lon, lat, gdp in cities:
        nodes.append({"名称": name, "类型": "周边城市",
                      "经度": lon, "纬度": lat, "GDP_亿元": gdp})
    return pd.DataFrame(nodes)


def gravity_matrix(nodes: pd.DataFrame) -> pd.DataFrame:
    """计算节点间物流联系强度矩阵（修正引力模型）。"""
    n = len(nodes)
    strength = pd.DataFrame(np.zeros((n, n)), index=nodes["名称"], columns=nodes["名称"])
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine(nodes.loc[i, "经度"], nodes.loc[i, "纬度"],
                          nodes.loc[j, "经度"], nodes.loc[j, "纬度"])
            d = max(d, 5.0)
            f = nodes.loc[i, "GDP_亿元"] * nodes.loc[j, "GDP_亿元"] / (d ** GAMMA)
            strength.iloc[i, j] = strength.iloc[j, i] = f
    return strength


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    nodes = build_nodes()
    S = gravity_matrix(nodes)

    # 阈值过滤：仅保留最强的边
    vals = S.values[np.triu_indices(len(S), 1)]
    thresh = np.quantile(vals, 1 - THRESHOLD_PCT)

    G = nx.Graph()
    for _, r in nodes.iterrows():
        G.add_node(r["名称"], 类型=r["类型"], GDP=r["GDP_亿元"])
    for i in range(len(S)):
        for j in range(i + 1, len(S)):
            w = S.iloc[i, j]
            if w >= thresh:
                G.add_edge(S.index[i], S.columns[j], weight=round(float(w), 1))

    # 中心性指标
    degree_c = nx.degree_centrality(G)
    between_c = nx.betweenness_centrality(G, weight="weight")
    eigen_c = nx.eigenvector_centrality_numpy(G, weight="weight")

    metrics = pd.DataFrame({
        "节点": list(G.nodes()),
        "类型": [G.nodes[n]["类型"] for n in G.nodes()],
        "度中心性": [round(degree_c[n], 4) for n in G.nodes()],
        "介数中心性": [round(between_c[n], 4) for n in G.nodes()],
        "特征向量中心性": [round(eigen_c[n], 4) for n in G.nodes()],
    }).sort_values("度中心性", ascending=False).reset_index(drop=True)
    metrics.to_csv(OUT_DIR / "network_metrics.csv", index=False, encoding="utf-8-sig")

    # 凝聚子群（社区检测）
    communities = community.greedy_modularity_communities(G, weight="weight")
    comm_map = {}
    for ci, comm in enumerate(communities):
        for node in comm:
            comm_map[node] = ci
    comm_df = pd.DataFrame([{"节点": k, "社区": v} for k, v in comm_map.items()])
    comm_df.to_csv(OUT_DIR / "network_communities.csv", index=False, encoding="utf-8-sig")

    # 网络可视化
    fig, ax = plt.subplots(figsize=(12, 9))
    pos = {r["名称"]: (r["经度"], r["纬度"]) for _, r in nodes.iterrows()}
    node_color = ["#d62728" if G.nodes[n]["类型"] == "区县" else "#1f77b4"
                  for n in G.nodes()]
    node_size = [300 + degree_c[n] * 4000 for n in G.nodes()]

    edges = list(G.edges(data=True))
    max_w = max(d["weight"] for _, _, d in edges)
    widths = [0.5 + 4 * d["weight"] / max_w for _, _, d in edges]

    nx.draw_networkx_edges(G, pos, ax=ax, width=widths, alpha=0.45, edge_color="gray")
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_color,
                           node_size=node_size, alpha=0.9)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=9,
                            font_family="Microsoft YaHei")
    ax.set_title("长沙区域物流空间网络（修正引力模型）")
    ax.set_xlabel("经度")
    ax.set_ylabel("纬度")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color="#d62728", label="区县"),
                       Patch(color="#1f77b4", label="周边城市")], loc="upper right")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "13_spatial_network.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    print("=== 区域物流空间网络分析完成 ===")
    print("核心枢纽（按度中心性排序前 5）：")
    print(metrics.head(5).to_string(index=False))
    print(f"\n识别到 {len(communities)} 个凝聚子群：")
    for ci, comm in enumerate(communities):
        print(f"  社区 {ci}: {list(comm)}")


if __name__ == "__main__":
    main()

