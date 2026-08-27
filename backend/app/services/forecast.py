# -*- coding: utf-8 -*-
"""forecast.py — 移动平均 + 线性趋势预测（预算执行、碳资产预警用，纯 Python）。"""


def moving_average(values, n: int = 3):
    if not values:
        return None
    tail = values[-n:]
    return sum(tail) / len(tail)


def linear_fit(values):
    """最小二乘拟合，返回 (slope, intercept)，x 取 0..n-1。"""
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    if n == 1:
        return 0.0, float(values[0])
    xm = (n - 1) / 2.0
    ym = sum(values) / n
    den = sum((i - xm) ** 2 for i in range(n))
    slope = sum((i - xm) * (y - ym) for i, y in enumerate(values)) / den if den else 0.0
    return slope, ym - slope * xm


def forecast_next(values, horizon: int = 1, ma_n: int = 3, blend: float = 0.5):
    """未来 horizon 期预测：移动平均基线 + 线性趋势加权混合。"""
    if not values or horizon <= 0:
        return []
    slope, intercept = linear_fit(values)
    base = moving_average(values, ma_n)
    n = len(values)
    result = []
    for i in range(1, horizon + 1):
        trend_value = intercept + slope * (n - 1 + i)
        ma_value = base + slope * i
        value = blend * trend_value + (1 - blend) * ma_value
        result.append(max(value, 0.0))
    return result


def forecast_total(values, horizon: int, ma_n: int = 3):
    """未来 horizon 期累计预测值。"""
    return sum(forecast_next(values, horizon, ma_n))
