# -*- coding: utf-8 -*-
"""optimizer.py — 规则引擎的设备运行参数优化建议（纯 Python）。

年运行小时 5500、平均负载率 0.72 作为缺省工况假设。
"""

ANNUAL_HOURS = 5500
LOAD_FACTOR = 0.72
ELECTRICITY_CE = 0.1229  # kgce/kWh

_CATEGORY_ADVICE = {
    "电炉": "提高炉衬保温与电极控制精度，减少热损失",
    "空压机": "下调出口压力设定值 0.05~0.1 MPa，治理管网泄漏",
    "水泵": "加装变频调速，按需求流量调节取代阀门节流",
    "风机": "变频改造并优化叶轮工况点",
    "加热炉": "回收烟气余热预热助燃空气",
    "default": "开展能效诊断，按设备能效标准更新改造",
}


def annual_consumption_kwh(rated_power: float) -> float:
    return rated_power * ANNUAL_HOURS * LOAD_FACTOR


def suggest(equipments):
    """equipments: [{id, name, category, org_code, rated_power, efficiency, standard_value}]。

    返回按预计节能量降序排列的建议列表。
    """
    suggestions = []
    for eq in equipments:
        eff, target = eq.get("efficiency", 0.0), eq.get("standard_value", 0.0)
        if not eff or target <= 0 or eff >= target:
            continue
        annual_kwh = annual_consumption_kwh(eq.get("rated_power", 0.0))
        saving_kwh = annual_kwh * (1.0 - eff / target)
        saving_tce = saving_kwh * ELECTRICITY_CE / 1000.0
        suggestions.append({
            "equipment": eq.get("name"),
            "category": eq.get("category"),
            "org_code": eq.get("org_code"),
            "current": {"运行效率(%)": round(eff, 2), "额定功率(kW)": round(eq.get("rated_power", 0.0), 1)},
            "suggested": {
                "运行效率(%)": round(target, 2),
                "措施": _CATEGORY_ADVICE.get(eq.get("category"), _CATEGORY_ADVICE["default"]),
            },
            "saving_kwh": round(saving_kwh, 0),
            "saving_tce": round(saving_tce, 2),
        })
    suggestions.sort(key=lambda s: s["saving_tce"], reverse=True)
    return suggestions
