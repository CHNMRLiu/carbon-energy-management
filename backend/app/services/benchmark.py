# -*- coding: utf-8 -*-
"""benchmark.py — 工序/产品/设备能效对标：实际值对照限额标准、达标率与建议（纯 Python）。"""
from sqlalchemy import select

from app.core.database import session_scope
from app.models.base import EnergyLimitStandard, Equipment, Organization
from app.models.statistics import MonthlySummary
from app.models.business import Production


def _latest_period():
    with session_scope("statistics") as s:
        row = s.execute(select(MonthlySummary.period).order_by(MonthlySummary.period.desc())).first()
    return row[0] if row else None


def _ytd_keys(anchor: str):
    year = anchor[:4]
    month = int(anchor[5:7])
    return [f"{year}-{m:02d}" for m in range(1, month + 1)]


def _item_row(category, code, name, actual, limit, unit, direction="le"):
    if direction == "ge":
        achieved = actual >= limit
        deviation = round((actual - limit) / limit * 100.0, 2) if limit else 0.0
        advice = "达标，保持当前运行水平" if achieved else f"低于标准 {abs(deviation)}%，建议检修提效或更新设备"
    else:
        achieved = actual <= limit
        deviation = round((actual - limit) / limit * 100.0, 2) if limit else 0.0
        advice = "达标，保持当前工艺参数" if achieved else f"超出限额 {deviation}%，建议优化工艺参数并排查高耗能环节"
    return {
        "category": category,
        "item_code": code,
        "item_name": name,
        "actual_value": round(actual, 2),
        "limit_value": round(limit, 2),
        "unit": unit,
        "direction": direction,
        "achieved": achieved,
        "deviation_pct": deviation,
        "advice": advice,
    }


def compute_items():
    """计算三类对标项（工序/产品/设备），返回 (anchor_period, items)。"""
    anchor = _latest_period()
    if not anchor:
        return None, []
    keys = _ytd_keys(anchor)

    # 限额标准
    with session_scope("base") as s:
        standards = s.scalars(select(EnergyLimitStandard)).all()
        equipments = s.scalars(select(Equipment)).all()
        orgs = {o.code: o.name for o in s.scalars(select(Organization)).all()}

    # 年初至今：车间折标煤(kgce)、产量
    ce_by_org, ce_by_energy = {}, {}
    with session_scope("statistics") as s:
        rows = s.scalars(select(MonthlySummary).where(MonthlySummary.period.in_(keys))).all()
    for r in rows:
        ce_by_org[r.org_code] = ce_by_org.get(r.org_code, 0.0) + r.ce_quantity * 1000.0
        ce_by_energy[r.energy_code] = ce_by_energy.get(r.energy_code, 0.0) + r.ce_quantity * 1000.0
    output_by_org, total_output = {}, 0.0
    with session_scope("business") as s:
        prods = s.scalars(select(Production).where(Production.period.in_(keys))).all()
    for p in prods:
        output_by_org[p.org_code] = output_by_org.get(p.org_code, 0.0) + p.output
        total_output += p.output

    items = []
    for std in standards:
        if std.category == "product":
            total_ce = sum(ce_by_org.values())
            if total_output:
                items.append(_item_row("product", std.item_code, std.item_name,
                                       total_ce / total_output, std.limit_value, std.unit, std.direction))
        elif std.category == "process":
            ce = ce_by_org.get(std.item_code, 0.0)
            out = output_by_org.get(std.item_code, 0.0)
            if out:
                items.append(_item_row("process", std.item_code, std.item_name,
                                       ce / out, std.limit_value, std.unit, std.direction))
    # 设备类：效率对照（越高越好）
    for eq in equipments:
        if eq.standard_value > 0:
            items.append(_item_row("equipment", f"EQ{eq.id:03d}", eq.name,
                                   eq.efficiency, eq.standard_value, "%", "ge"))
    return anchor, items


def summarize(items):
    total = len(items)
    achieved = sum(1 for i in items if i["achieved"])
    return {
        "total": total,
        "achieved": achieved,
        "rate": round(achieved / total * 100.0, 2) if total else 0.0,
    }
