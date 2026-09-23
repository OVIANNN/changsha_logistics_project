# -*- coding: utf-8 -*-
"""
matplotlib 中文显示共享配置模块
================================
统一注册系统中文字体，避免各脚本重复配置，保证图表中文正常显示。
所有绘图脚本在导入 matplotlib 后调用 setup_chinese_font() 即可。
"""

from pathlib import Path
import matplotlib
from matplotlib import font_manager as fm

# Windows 常见中文字体文件路径（按优先级）
_CANDIDATE_FONTS = [
    "C:/Windows/Fonts/msyh.ttc",        # 微软雅黑
    "C:/Windows/Fonts/simhei.ttf",      # 黑体
    "C:/Windows/Fonts/simsun.ttc",      # 宋体
    "C:/Windows/Fonts/NotoSansSC-Regular.otf",  # Noto Sans SC
]

# 已注册的字体名称（供 rcParams 使用）
_registered_name = None


def setup_chinese_font() -> str:
    """注册并启用中文字体，返回实际使用的字体名称。"""
    global _registered_name
    if _registered_name is not None:
        _apply(_registered_name)
        return _registered_name

    # 尝试注册系统字体文件
    for fp in _CANDIDATE_FONTS:
        if Path(fp).exists():
            try:
                fm.fontManager.addfont(fp)
                name = fm.FontProperties(fname=fp).get_name()
                _apply(name)
                _registered_name = name
                return name
            except Exception:
                continue

    # 兜底：直接使用已识别的常见字体名
    for name in ["Microsoft YaHei", "SimHei", "Noto Sans SC", "SimSun"]:
        if name in {f.name for f in fm.fontManager.ttflist}:
            _apply(name)
            _registered_name = name
            return name

    _registered_name = "DejaVu Sans"
    return _registered_name


def _apply(name: str):
    """应用字体配置。"""
    matplotlib.rcParams["font.sans-serif"] = [name, "Microsoft YaHei",
                                              "SimHei", "Noto Sans SC",
                                              "DejaVu Sans"]
    matplotlib.rcParams["font.family"] = "sans-serif"
    matplotlib.rcParams["axes.unicode_minus"] = False
