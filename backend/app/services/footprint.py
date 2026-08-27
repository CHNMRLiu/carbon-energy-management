# -*- coding: utf-8 -*-
"""footprint.py — GB/T 24067 产品碳足迹：五阶段核算与碳标识等级（纯 Python）。"""

STAGES = [
    ("raw_material", "原材料获取"),
    ("production", "生产制造"),
    ("transport", "运输配送"),
    ("use", "使用阶段"),
    ("recycle", "回收处置"),
]
_STAGE_NAMES = dict(STAGES)


def stage_summary(records):
    """records: [{stage, emission}] → 各阶段合计与占比。"""
    total = sum(r["emission"] for r in records) or 0.0
    agg = {}
    for r in records:
        agg[r["stage"]] = agg.get(r["stage"], 0.0) + r["emission"]
    rows = []
    for code, name in STAGES:
        value = agg.get(code, 0.0)
        rows.append({
            "stage": code,
            "stage_name": name,
            "emission": round(value, 2),
            "share": round(value / total * 100.0, 2) if total else 0.0,
        })
    return round(total, 2), rows


def unit_footprint(total_tco2: float, output_t: float):
    """单位产品碳足迹 kgCO2e/单位。"""
    if not output_t:
        return None
    return round(total_tco2 * 1000.0 / output_t, 3)


def carbon_label(unit_kgco2e, benchmark: float = 180.0):
    """碳标识等级：以基准值划分 A(优秀)/B(良好)/C(一般)/D(偏高)。"""
    if unit_kgco2e is None:
        return {"grade": "-", "description": "数据不足", "benchmark": benchmark}
    if unit_kgco2e <= benchmark * 0.75:
        grade, desc = "A", "一级（国际先进）"
    elif unit_kgco2e <= benchmark:
        grade, desc = "B", "二级（国内先进）"
    elif unit_kgco2e <= benchmark * 1.3:
        grade, desc = "C", "三级（行业平均）"
    else:
        grade, desc = "D", "四级（偏高，需改进）"
    return {"grade": grade, "description": desc, "benchmark": benchmark}
