#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Matplotlib + Seaborn initialization with CJK font support.

Usage:
    from setup_matplotlib import init_plot_env
    init_plot_env()

    # If you need to change seaborn style/theme later in your code:
    from setup_matplotlib import safe_set_style, safe_set_theme
    safe_set_style("darkgrid")
    safe_set_theme(style="white", context="talk")
"""
import platform
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm


def _detect_cjk_font():
    """Detect the best available CJK font for the current platform."""
    system = platform.system()

    if system == "Darwin":
        font_candidates = [
            'Arial Unicode MS', 'PingFang SC', 'PingFang HK',
            'Heiti TC', 'Heiti SC', 'STHeiti', 'Hiragino Sans GB',
        ]
    elif system == "Windows":
        font_candidates = ['Microsoft YaHei', 'SimHei', 'SimSun']
    else:
        font_candidates = [
            'Noto Sans CJK SC', 'WenQuanYi Zen Hei',
            'WenQuanYi Micro Hei', 'Droid Sans Fallback',
        ]

    available = {f.name for f in fm.fontManager.ttflist}
    for name in font_candidates:
        if name in available:
            return name
    return None


def _apply_cjk_font():
    """Apply CJK font to current rcParams. Returns the chosen font name."""
    chosen = _detect_cjk_font()
    if chosen:
        plt.rcParams['font.sans-serif'] = [chosen] + plt.rcParams['font.sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
    return chosen


def init_plot_env(seaborn_style="whitegrid"):
    """Initialize matplotlib + seaborn with proper CJK font support.

    This function MUST be called instead of manually calling sns.set_theme(),
    sns.set_style(), or configuring fonts separately, because these seaborn
    functions reset rcParams and would override any font settings.

    Args:
        seaborn_style: seaborn theme style, default "whitegrid"
    Returns:
        The chosen CJK font name, or None if no CJK font was found.
    """
    import seaborn as sns
    sns.set_theme(style=seaborn_style)
    return _apply_cjk_font()


def safe_set_style(style="whitegrid"):
    """Safe replacement for sns.set_style() that preserves CJK font settings.

    Use this instead of sns.set_style() when you need to change the style
    after init_plot_env() has been called.

    Args:
        style: seaborn style name ("whitegrid", "darkgrid", "white", "dark", "ticks")
    """
    import seaborn as sns
    sns.set_style(style)
    _apply_cjk_font()


def safe_set_theme(style="whitegrid", **kwargs):
    """Safe replacement for sns.set_theme() that preserves CJK font settings.

    Use this instead of sns.set_theme() when you need to change the theme
    after init_plot_env() has been called.

    Args:
        style: seaborn style name
        **kwargs: additional arguments passed to sns.set_theme()
    """
    import seaborn as sns
    sns.set_theme(style=style, **kwargs)
    _apply_cjk_font()
