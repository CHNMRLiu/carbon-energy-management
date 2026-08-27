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


# ---------- 1.1 单器具曲线查询（新增） ----------
from app.models.collection import MeterPoint, MeterReading, ManualReport

@router.get("/energy/meter-curve")
def meter_curve(
    point_code: str = Query(..., description="计量点编码"),
    period: str = Query("day", description="统计周期：day/week/month/year"),
    start: str = Query(None, description="开始日期 YYYY-MM-DD 或 YYYY-MM 或 YYYY"),
    end: str = Query(None, description="结束日期 YYYY-MM-DD 或 YYYY-MM 或 YYYY"),
    dimension: str = Query("energy", description="统计维度：energy/cost/carbon"),
):
    """
    单器具消耗曲线查询
    - period: day/week/month/year
    - dimension: energy(能耗)/cost(成本)/carbon(碳排放)
    """
    # 查找计量点
    with session_scope("collection") as s:
        point = s.scalars(select(MeterPoint).where(MeterPoint.code == point_code)).first()
    if not point:
        return fail(40401, f"计量点 {point_code} 不存在")

    # 根据周期构建时间范围
    from datetime import datetime, timedelta
    now = datetime.now()
    if period == "day":
        # 近7天
        days = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
        data_key = "%Y-%m-%d"
    elif period == "week":
        # 近8周
        weeks = []
        for i in range(7, -1, -1):
            monday = now - timedelta(days=now.weekday() + i * 7)
            weeks.append(monday.strftime("%Y-W%W"))
        data_key = "%Y-W%W"
    elif period == "month":
        # 近12个月
        months = [energy_calc.shift_month(now.strftime("%Y-%m"), -i) for i in range(11, -1, -1)]
        data_key = "%Y-%m"
    elif period == "year":
        # 近5年
        years = [str(now.year - i) for i in range(4, -1, -1)]
        data_key = "%Y"
    else:
        return fail(40002, f"不支持的周期类型：{period}")

    # 获取该计量点的读数
    with session_scope("collection") as s:
        readings = s.scalars(
            select(MeterReading).where(MeterReading.point_id == point.id)
        ).all()

    # 按周期聚合
    agg_data = {}
    for r in readings:
        key = r.ts.strftime(data_key)
        agg_data[key] = agg_data.get(key, 0.0) + r.value

    # 构建返回数据（补全缺失周期为0）
    result = []
    emap = _energy_map()
    energy_info = emap.get(point.energy_code, {})
    ce_coeff = energy_info.get("ce", 0.0)
    price = energy_info.get("price", 0.0)
    factor = 0.0
    
    # 从 base.db 获取排放因子
    from app.models.base import EmissionFactor
    with session_scope("base") as s:
        ef_row = s.scalars(
            select(EmissionFactor).where(EmissionFactor.energy_code == point.energy_code)
        ).first()
        if ef_row:
            factor = ef_row.factor

    time_labels = days if period == "day" else (weeks if period == "week" else (months if period == "month" else years))
    for label in time_labels:
        value = agg_data.get(label, 0.0)
        if dimension == "energy":
            # 折标煤
            display_value = round(value * ce_coeff / 1000.0, 4) if ce_coeff else round(value, 2)
            unit = "tce" if ce_coeff else point.unit
        elif dimension == "cost":
            # 成本
            display_value = round(value * price, 2)
            unit = "元"
        elif dimension == "carbon":
            # 碳排放
            display_value = round(value * factor, 4)
            unit = "tCO₂"
        else:
            return fail(40003, f"不支持的维度类型：{dimension}")
        
        result.append({
            "time": label,
            "value": display_value,
            "unit": unit
        })

    return ok({
        "point_code": point_code,
        "point_name": point.name,
        "energy_code": point.energy_code,
        "energy_name": energy_info.get("name", point.energy_code),
        "period": period,
        "dimension": dimension,
        "data": result
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


# ---------- 7 能源分析增强 - 计量对标/计量环比/单元对标 ----------
from app.models.collection import MeterPoint, MeterReading


@router.get("/energy/meter-comparison")
def meter_comparison(
    meter1_id: int = Query(..., description="计量点1 ID"),
    meter2_id: int = Query(..., description="计量点2 ID"),
    period: str = Query("month", description="统计周期: day/week/month/year"),
    start: str = Query(None, description="起始时间 YYYY-MM-DD"),
    end: str = Query(None, description="结束时间 YYYY-MM-DD"),
):
    """两计量器具同时段对比分析"""
    from datetime import datetime, timedelta
    
    # 获取两个计量点信息
    with session_scope("base") as s:
        meter1 = s.get(MeterPoint, meter1_id)
        meter2 = s.get(MeterPoint, meter2_id)
    
    if not meter1 or not meter2:
        return fail(40401, "计量点不存在")
    
    # 确定时间范围
    now = datetime.now()
    if period == "day":
        # 近30天
        days = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(29, -1, -1)]
        data_key = "%Y-%m-%d"
    elif period == "week":
        # 近12周
        weeks = []
        for i in range(11, -1, -1):
            d = now - timedelta(weeks=i)
            weeks.append(d.strftime("%Y-W%W"))
        data_key = "%Y-W%W"
    elif period == "month":
        # 近12个月
        months = [energy_calc.shift_month(now.strftime("%Y-%m"), -i) for i in range(11, -1, -1)]
        data_key = "%Y-%m"
    elif period == "year":
        # 近5年
        years = [str(now.year - i) for i in range(4, -1, -1)]
        data_key = "%Y"
    else:
        return fail(40002, f"不支持的周期类型：{period}")
    
    # 获取两个计量点的读数
    with session_scope("collection") as s:
        readings1 = s.scalars(
            select(MeterReading).where(MeterReading.point_id == meter1_id)
        ).all()
        readings2 = s.scalars(
            select(MeterReading).where(MeterReading.point_id == meter2_id)
        ).all()
    
    # 按周期聚合
    def aggregate(readings):
        agg = {}
        for r in readings:
            key = r.ts.strftime(data_key)
            agg[key] = agg.get(key, 0.0) + r.value
        return agg
    
    agg1 = aggregate(readings1)
    agg2 = aggregate(readings2)
    
    # 构建返回数据
    emap = _energy_map()
    time_labels = days if period == "day" else (weeks if period == "week" else (months if period == "month" else years))
    
    series1 = []
    series2 = []
    for label in time_labels:
        series1.append(round(agg1.get(label, 0.0), 2))
        series2.append(round(agg2.get(label, 0.0), 2))
    
    total1 = sum(series1)
    total2 = sum(series2)
    diff = total1 - total2
    diff_pct = round(abs(diff) / max(total1, total2) * 100, 2) if max(total1, total2) > 0 else 0
    
    return ok({
        "meter1": {
            "id": meter1.id,
            "code": meter1.code,
            "name": meter1.name,
            "energy_code": meter1.energy_code,
            "energy_name": emap.get(meter1.energy_code, {}).get("name", meter1.energy_code),
            "unit": meter1.unit,
            "total": round(total1, 2),
            "series": series1
        },
        "meter2": {
            "id": meter2.id,
            "code": meter2.code,
            "name": meter2.name,
            "energy_code": meter2.energy_code,
            "energy_name": emap.get(meter2.energy_code, {}).get("name", meter2.energy_code),
            "unit": meter2.unit,
            "total": round(total2, 2),
            "series": series2
        },
        "comparison": {
            "difference": round(diff, 2),
            "diff_percent": diff_pct,
            "higher": "meter1" if total1 > total2 else "meter2",
            "time_labels": time_labels
        }
    })


@router.get("/energy/meter-trend")
def meter_trend(
    meter_id: int = Query(..., description="计量点 ID"),
    period: str = Query("month", description="对比周期: month-over-month/year-over-year"),
):
    """同一计量器具不同时段对比（环比/同比）"""
    from datetime import datetime, timedelta
    
    # 获取计量点信息
    with session_scope("base") as s:
        meter = s.get(MeterPoint, meter_id)
    
    if not meter:
        return fail(40401, "计量点不存在")
    
    now = datetime.now()
    
    if period == "month-over-month":
        # 本月 vs 上月
        current_label = now.strftime("%Y-%m")
        prev_label = energy_calc.shift_month(current_label, -1)
        labels = [prev_label, current_label]
        period_names = ["上月", "本月"]
    elif period == "year-over-year":
        # 今年 vs 去年
        current_year = str(now.year)
        prev_year = str(now.year - 1)
        labels = [prev_year, current_year]
        period_names = ["去年", "今年"]
    else:
        return fail(40002, f"不支持的对比类型：{period}")
    
    # 获取读数
    with session_scope("collection") as s:
        readings = s.scalars(
            select(MeterReading).where(MeterReading.point_id == meter_id)
        ).all()
    
    # 按周期聚合
    data_key = "%Y-%m" if period == "month-over-month" else "%Y"
    agg = {}
    for r in readings:
        key = r.ts.strftime(data_key)
        agg[key] = agg.get(key, 0.0) + r.value
    
    values = [round(agg.get(labels[0], 0.0), 2), round(agg.get(labels[1], 0.0), 2)]
    change = values[1] - values[0]
    change_pct = round(change / values[0] * 100, 2) if values[0] > 0 else 0
    
    emap = _energy_map()
    
    return ok({
        "meter": {
            "id": meter.id,
            "code": meter.code,
            "name": meter.name,
            "energy_code": meter.energy_code,
            "energy_name": emap.get(meter.energy_code, {}).get("name", meter.energy_code),
            "unit": meter.unit
        },
        "trend": {
            "period_type": period,
            "period_names": period_names,
            "values": values,
            "change": round(change, 2),
            "change_percent": change_pct
        }
    })


@router.get("/energy/unit-comparison")
def unit_comparison(
    unit1_code: str = Query(..., description="用能单元1编码"),
    unit2_code: str = Query(..., description="用能单元2编码"),
    period: str = Query("month", description="统计周期: day/week/month/year"),
):
    """两用能单元同时段对比"""
    from datetime import datetime, timedelta
    from app.models.base import Organization
    
    # 获取两个用能单元信息
    with session_scope("base") as s:
        unit1 = s.execute(select(Organization).where(Organization.code == unit1_code)).first()
        unit2 = s.execute(select(Organization).where(Organization.code == unit2_code)).first()
    
    if not unit1 or not unit2:
        return fail(40401, "用能单元不存在")
    
    unit1 = unit1[0]
    unit2 = unit2[0]
    
    now = datetime.now()
    
    # 确定时间范围
    if period == "day":
        keys = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(29, -1, -1)]
    elif period == "week":
        keys = []
        for i in range(11, -1, -1):
            d = now - timedelta(weeks=i)
            keys.append(d.strftime("%Y-W%W"))
    elif period == "month":
        keys = [energy_calc.shift_month(now.strftime("%Y-%m"), -i) for i in range(11, -1, -1)]
    elif period == "year":
        keys = [str(now.year - i) for i in range(4, -1, -1)]
    else:
        return fail(40002, f"不支持的周期类型：{period}")
    
    # 获取两个单元的月度汇总数据
    rows1 = _monthly_rows(keys, org_code=unit1_code)
    rows2 = _monthly_rows(keys, org_code=unit2_code)
    
    emap = _energy_map()
    
    # 按能源类型聚合
    def aggregate_by_energy(rows):
        result = {}
        for r in rows:
            code = r.energy_code
            if code not in result:
                result[code] = {
                    "energy_code": code,
                    "energy_name": emap.get(code, {}).get("name", code),
                    "unit": emap.get(code, {}).get("unit", ""),
                    "quantity": 0.0,
                    "ce_quantity": 0.0
                }
            result[code]["quantity"] += r.quantity
            result[code]["ce_quantity"] += r.ce_quantity
        return list(result.values())
    
    details1 = aggregate_by_energy(rows1)
    details2 = aggregate_by_energy(rows2)
    
    total_ce1 = sum(d["ce_quantity"] for d in details1)
    total_ce2 = sum(d["ce_quantity"] for d in details2)
    diff = total_ce1 - total_ce2
    diff_pct = round(abs(diff) / max(total_ce1, total_ce2) * 100, 2) if max(total_ce1, total_ce2) > 0 else 0
    
    return ok({
        "unit1": {
            "code": unit1.code,
            "name": unit1.name,
            "total_ce_tce": round(total_ce1, 2),
            "details": details1
        },
        "unit2": {
            "code": unit2.code,
            "name": unit2.name,
            "total_ce_tce": round(total_ce2, 2),
            "details": details2
        },
        "comparison": {
            "difference": round(diff, 2),
            "diff_percent": diff_pct,
            "higher": "unit1" if total_ce1 > total_ce2 else "unit2"
        }
    })
