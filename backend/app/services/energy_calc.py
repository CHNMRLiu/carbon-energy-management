# -*- coding: utf-8 -*-
"""energy_calc.py — GB/T 2589 折标煤换算与能耗强度计算内核（纯 Python）。"""
from datetime import datetime

from dateutil.relativedelta import relativedelta


# ---------- 折标煤 ----------
def kgce(quantity: float, coefficient: float) -> float:
    """实物量 × 折标系数 → kgce。"""
    return float(quantity) * float(coefficient)


def to_tce(quantity: float, coefficient: float) -> float:
    """实物量 → 吨标准煤。"""
    return kgce(quantity, coefficient) / 1000.0


# ---------- 期间工具 ----------
def _to_month(token: str):
    """'2026-08' / '2026-8' / '2026' → 当月 1 号 datetime；空 → None。"""
    if not token:
        return None
    token = str(token).strip()
    if len(token) == 4:
        return datetime(int(token), 1, 1)
    parts = token.split("-")
    return datetime(int(parts[0]), int(parts[1]), 1)


def period_keys(period: str = "month", start=None, end=None):
    """生成区间内期间键列表。month → ['YYYY-MM']；year → ['YYYY']。"""
    now = datetime.now()
    if period == "year":
        end_dt = _to_month(end) or datetime(now.year, 1, 1)
        start_dt = _to_month(start) or datetime(max(end_dt.year - 2, 2024), 1, 1)
        return [str(y) for y in range(start_dt.year, end_dt.year + 1)]
    end_dt = _to_month(end) or datetime(now.year, now.month, 1)
    start_dt = _to_month(start) or (end_dt - relativedelta(months=11))
    keys, cur = [], start_dt
    while cur <= end_dt:
        keys.append(cur.strftime("%Y-%m"))
        cur += relativedelta(months=1)
    return keys


def shift_month(period_key: str, delta: int) -> str:
    """'2026-08' 偏移 delta 个月。"""
    dt = _to_month(period_key) + relativedelta(months=delta)
    return dt.strftime("%Y-%m")


# ---------- 强度指标 ----------
def unit_product_energy(total_tce: float, output_t: float):
    """单位产品综合能耗 kgce/t。"""
    if not output_t:
        return None
    return round(total_tce * 1000.0 / output_t, 2)


def unit_value_energy(total_tce: float, output_value_wan: float):
    """单位产值综合能耗 tce/万元。"""
    if not output_value_wan:
        return None
    return round(total_tce / output_value_wan, 4)


def change_rate(current, previous):
    """同比/环比变化率（%），基数无效返回 None。"""
    if current is None or previous in (None, 0):
        return None
    return round((current - previous) / abs(previous) * 100.0, 2)
