# -*- coding: utf-8 -*-
"""统一的 matplotlib 中文字体配置——防止图中汉字变方框(tofu)。
两机通用：Linux 用 Noto Sans CJK SC（已装），macOS 用 PingFang SC。
用法：在任何出图脚本开头  `import hy7_mpl_cjk`（或 `from hy7_mpl_cjk import use_cjk; use_cjk()`）。
注意：CLAUDE.md 仍建议「可能在 Linux 跑的科学图表优先用英文标签」；本模块是当确需中文时的保险。
"""
import matplotlib

_CANDIDATES = [
    "Noto Sans CJK SC",   # Linux (hy7-linux 已装)
    "Noto Sans CJK JP",
    "WenQuanYi Micro Hei",
    "PingFang SC",        # macOS
    "Heiti SC", "Arial Unicode MS",
    "DejaVu Sans",        # 兜底(无 CJK，但不报错)
]

def use_cjk():
    from matplotlib import font_manager
    have = {f.name for f in font_manager.fontManager.ttflist}
    chosen = [n for n in _CANDIDATES if n in have] or ["DejaVu Sans"]
    matplotlib.rcParams["font.sans-serif"] = chosen + matplotlib.rcParams.get("font.sans-serif", [])
    matplotlib.rcParams["axes.unicode_minus"] = False
    return chosen[0]

_active = use_cjk()
