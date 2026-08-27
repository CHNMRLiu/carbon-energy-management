# -*- coding: utf-8 -*-
"""能耗业务 API：能耗查询/消费量与强度/分析与策略/能效对标/能流分析/能效优化。"""
import re

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.core.database import session_scope
from app.core.response import ok, fail
from app.models.base import EnergyType, Equipment
from app.models.statistics import MonthlySummary
from app.models.business import Production, EnergyBill
from app.services import energy_calc, benchmark as benchmark_svc, sankey as sankey_svc
from app.services import optimizer, strategy

router = APIRouter(tags=["能耗管理"])

_PERIOD_TOKEN_RE = re.compile(r"^\d{4}(-\d{1,2})?$")


# ---------- 公共工具 ----------
def _energy_map():
    with session_scope("base") as s:
        rows = s.scalars(select(EnergyType)).all()
    return {r.code: {"name": r.name, "unit": r.unit, "ce": r.ce_coefficient, "price": r.price} for r in rows}


def _latest_month():
    with session_scope("statistics") as s:
        row = s.execute(select(MonthlySummary.period).order_by(MonthlySummary.period.desc())).first()
    return row[0] if row else None


def _monthly_rows(keys, energy_type="all", org_code=None):
    with session_scope("statistics") as s:
        stmt = select(MonthlySummary).where(MonthlySummary.period.in_(keys))
        if energy_type and energy_type != "all":
            stmt = stmt.where(MonthlySummary.energy_code == energy_type)
        if org_code:
            stmt = stmt.where(MonthlySummary.org_code == org_code)
        return s.scalars(stmt).all()


def _production_totals(keys):
    with session_scope("business") as s:
        rows = s.scalars(select(Production).where(Production.period.in_(keys))).all()
    return sum(r.output for r in rows), sum(r.output_value for r in rows)


def _sum_ce(rows):
    return sum(r.ce_quantity for r in rows)


def _last12_keys(anchor=None):
    anchor = anchor or _latest_month()
    return [energy_calc.shift_month(anchor, -i) for i in range(11, -1, -1)]


# ---------- 1 能耗查询 ----------
@router.get("/energy/consumption")
def energy_consumption(
    energy_type: str = Query("all"),
    period: str = Query("month"),
    start: str = Query(None),
    end: str = Query(None),
):
    for name, value in (("start", start), ("end", end)):
        if value and not _PERIOD_TOKEN_RE.match(value):
            return JSONResponse(
                status_code=400,
                content=fail(40001, f"参数 {name} 格式非法：应为 YYYY 或 YYYY-MM，当前值 {value!r}"),
            )
    keys = energy_calc.period_keys(period, start, end)
    if period == "year":
        month_keys = [f"{y}-{m:02d}" for y in keys for m in range(1, 13)]
        rows = _monthly_rows(month_keys, energy_type)
        group_of = lambda p: p[:4]
    else:
        rows = _monthly_rows(keys, energy_type)
        group_of = lambda p: p
    emap = _energy_map()

    details, trend = {}, {}
    for r in rows:
        d = details.setdefault(r.energy_code, {"quantity": 0.0, "ce": 0.0})
        d["quantity"] += r.quantity
        d["ce"] += r.ce_quantity
        t = trend.setdefault(group_of(r.period), {"total": 0.0, "by_energy": {}})
        t["total"] += r.ce_quantity
        t["by_energy"][r.energy_code] = t["by_energy"].get(r.energy_code, 0.0) + r.ce_quantity

    return ok({
        "period": period,
        "range": [keys[0], keys[-1]] if keys else [],
        "details": [
            {
                "energy_code": code,
                "energy_name": emap.get(code, {}).get("name", code),
                "unit": emap.get(code, {}).get("unit", ""),
                "quantity": round(v["quantity"], 1),
                "ce_tce": round(v["ce"], 2),
            }
            for code, v in sorted(details.items(), key=lambda kv: kv[1]["ce"], reverse=True)
        ],
        "total_tce": round(sum(v["ce"] for v in details.values()), 2),
        "trend": [
            {"period": g, "total_tce": round(t["total"], 2),
             "by_energy": {c: round(x, 2) for c, x in t["by_energy"].items()}}
            for g, t in sorted(trend.items())
        ],
    })


# ---------- 2 消费量与强度 ----------
@router.get("/energy/calculation")
def energy_calculation(period: str = Query("month")):
    anchor = _latest_month()
    if not anchor:
        return ok({"message": "暂无数据"})

    if period == "year":
        year = anchor[:4]
        month_n = int(anchor[5:7])
        cur_keys = [f"{year}-{m:02d}" for m in range(1, month_n + 1)]
        prev_keys = None
        yoy_keys = [f"{int(year) - 1}-{m:02d}" for m in range(1, month_n + 1)]
        cur_label, yoy_label = f"{year}年累计", f"{int(year) - 1}年同期"
    else:
        cur_keys = [anchor]
        prev_keys = [energy_calc.shift_month(anchor, -1)]
        yoy_keys = [energy_calc.shift_month(anchor, -12)]
        cur_label, yoy_label = anchor, energy_calc.shift_month(anchor, -12)

    def totals(keys):
        ce = _sum_ce(_monthly_rows(keys))
        output_t, output_value = _production_totals(keys)
        return ce, output_t, output_value

    cur_ce, cur_out, cur_val = totals(cur_keys)
    yoy_ce, yoy_out, yoy_val = totals(yoy_keys) if yoy_keys else (None, None, None)
    prev_ce, prev_out, prev_val = totals(prev_keys) if prev_keys else (None, None, None)

    cur_upe = energy_calc.unit_product_energy(cur_ce, cur_out)
    yoy_upe = energy_calc.unit_product_energy(yoy_ce, yoy_out) if yoy_ce is not None else None
    prev_upe = energy_calc.unit_product_energy(prev_ce, prev_out) if prev_ce is not None else None
    cur_uve = energy_calc.unit_value_energy(cur_ce, cur_val)
    yoy_uve = energy_calc.unit_value_energy(yoy_ce, yoy_val) if yoy_ce is not None else None
    prev_uve = energy_calc.unit_value_energy(prev_ce, prev_val) if prev_ce is not None else None

    return ok({
        "period": period,
        "current_period": cur_label,
        "comprehensive_energy": {
            "value": round(cur_ce, 2), "unit": "tce",
            "yoy": energy_calc.change_rate(cur_ce, yoy_ce),
            "mom": energy_calc.change_rate(cur_ce, prev_ce),
        },
        "unit_product_energy": {
            "value": cur_upe, "unit": "kgce/t",
            "yoy": energy_calc.change_rate(cur_upe, yoy_upe),
            "mom": energy_calc.change_rate(cur_upe, prev_upe),
        },
        "unit_value_energy": {
            "value": cur_uve, "unit": "tce/万元",
            "yoy": energy_calc.change_rate(cur_uve, yoy_uve),
            "mom": energy_calc.change_rate(cur_uve, prev_uve),
        },
        "output": {"output_t": round(cur_out, 1), "output_value_wan": round(cur_val, 1)},
        "compare_labels": {"yoy": yoy_label, "mom": prev_keys[0] if prev_keys else None},
    })


# ---------- 3 分析与策略 ----------
@router.get("/energy/analysis")
def energy_analysis():
    anchor = _latest_month()
    if not anchor:
        return ok({"range": [], "structure": [], "cost": [], "total_cost": 0.0,
                   "total_tce": 0.0, "efficiency_trend": [], "strategies": [],
                   "message": "暂无数据"})
    keys = _last12_keys(anchor)
    rows = _monthly_rows(keys)
    emap = _energy_map()

    ce_total = _sum_ce(rows)
    struct_agg, cost_agg = {}, {}
    with session_scope("business") as s:
        bills = s.scalars(select(EnergyBill).where(EnergyBill.period.in_(keys))).all()
    for b in bills:
        cost_agg[b.energy_code] = cost_agg.get(b.energy_code, 0.0) + b.cost
    for r in rows:
        struct_agg[r.energy_code] = struct_agg.get(r.energy_code, 0.0) + r.ce_quantity
    total_cost = sum(cost_agg.values())

    structure = sorted(
        [{"energy_code": c, "energy_name": emap.get(c, {}).get("name", c), "ce_tce": round(v, 2),
          "share": round(v / ce_total * 100.0, 2) if ce_total else 0.0}
         for c, v in struct_agg.items()],
        key=lambda x: x["ce_tce"], reverse=True)
    cost_rows = sorted(
        [{"energy_code": c, "energy_name": emap.get(c, {}).get("name", c), "cost": round(v, 0),
          "share": round(v / total_cost * 100.0, 2) if total_cost else 0.0}
         for c, v in cost_agg.items()],
        key=lambda x: x["cost"], reverse=True)

    # 能效趋势：逐月单位产品能耗
    output_by_month = {}
    with session_scope("business") as s:
        prods = s.scalars(select(Production).where(Production.period.in_(keys))).all()
    for p in prods:
        output_by_month[p.period] = output_by_month.get(p.period, 0.0) + p.output
    ce_by_month = {}
    for r in rows:
        ce_by_month[r.period] = ce_by_month.get(r.period, 0.0) + r.ce_quantity
    efficiency_trend = [
        {"period": k, "value": energy_calc.unit_product_energy(ce_by_month.get(k, 0.0), output_by_month.get(k, 0.0))}
        for k in keys
    ]

    _, benchmark_items = benchmark_svc.compute_items()
    suggestions = strategy.recommend(structure, cost_rows, efficiency_trend, benchmark_items)

    return ok({
        "range": [keys[0], keys[-1]],
        "structure": structure,
        "cost": cost_rows,
        "total_cost": round(total_cost, 0),
        "total_tce": round(ce_total, 2),
        "efficiency_trend": efficiency_trend,
        "strategies": suggestions,
    })


# ---------- 4 能效对标 ----------
@router.get("/energy/benchmark")
def energy_benchmark():
    anchor, items = benchmark_svc.compute_items()
    return ok({
        "period": f"{anchor[:4]}年累计" if anchor else None,
        "items": items,
        "summary": benchmark_svc.summarize(items),
    })


# ---------- 5 能流分析 ----------
@router.get("/energy/flow")
def energy_flow():
    anchor = _latest_month()
    if not anchor:
        return ok({"range": [], "unit": "tce", "total_input": 0.0,
                   "nodes": [], "links": [], "message": "暂无数据"})
    keys = _last12_keys(anchor)
    rows = _monthly_rows(keys)
    emap = _energy_map()
    ce_map = {}
    for r in rows:
        ce_map[r.energy_code] = ce_map.get(r.energy_code, 0.0) + r.ce_quantity
    names = {c: v["name"] for c, v in emap.items()}
    nodes, links, total = sankey_svc.build(ce_map, names)
    return ok({
        "range": [keys[0], keys[-1]],
        "unit": "tce",
        "total_input": total,
        "nodes": nodes,
        "links": links,
    })


# ---------- 6 能效优化 ----------
@router.get("/energy/optimization")
def energy_optimization():
    with session_scope("base") as s:
        equipments = s.scalars(select(Equipment)).all()
    eq_dicts = [
        {"id": e.id, "name": e.name, "category": e.category, "org_code": e.org_code,
         "rated_power": e.rated_power, "efficiency": e.efficiency, "standard_value": e.standard_value}
        for e in equipments
    ]
    suggestions = optimizer.suggest(eq_dicts)
    return ok({
        "suggestions": suggestions,
        "total_saving_tce": round(sum(s["saving_tce"] for s in suggestions), 2),
        "total_saving_kwh": round(sum(s["saving_kwh"] for s in suggestions), 0),
        "equipment_count": len(eq_dicts),
    })
