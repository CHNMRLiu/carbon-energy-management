# -*- coding: utf-8 -*-
"""carbon_calc.py — GB/T 32151 排放因子法核算内核（纯 Python）。"""


def emission_of(quantity: float, factor: float) -> float:
    """活动水平 × 排放因子 → tCO2。"""
    return float(quantity) * float(factor)


def carbon_intensity(total_tco2: float, output_t: float):
    """碳排放强度 tCO2/t 产品。"""
    if not output_t:
        return None
    return round(total_tco2 / output_t, 4)


def breakdown(emission_map: dict, names: dict):
    """按能源来源拆分：[{energy_code, energy_name, emission, share}]。"""
    total = sum(emission_map.values())
    rows = []
    for code, value in emission_map.items():
        rows.append({
            "energy_code": code,
            "energy_name": names.get(code, code),
            "emission": round(value, 2),
            "share": round(value / total * 100.0, 2) if total else 0.0,
        })
    rows.sort(key=lambda r: r["emission"], reverse=True)
    return round(total, 2), rows


def monthly_overrun_alerts(monthly: list, monthly_budget: float):
    """月度排放超预算份额预警。monthly: [{period, emission}]。"""
    alerts = []
    if not monthly_budget:
        return alerts
    for row in monthly:
        if row["emission"] > monthly_budget:
            over = round((row["emission"] - monthly_budget) / monthly_budget * 100.0, 1)
            alerts.append({
                "period": row["period"],
                "level": "critical" if over > 10 else "warning",
                "message": f"{row['period']} 碳排放 {round(row['emission'],1)} tCO2，超出月度预算份额 {over}%",
            })
    return alerts
