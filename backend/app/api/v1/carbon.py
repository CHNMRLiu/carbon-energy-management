# -*- coding: utf-8 -*-
"""碳业务 API：预算/核算/足迹/供应链/核查/导出/资产。"""
from fastapi import APIRouter, Query
from fastapi.responses import Response
from sqlalchemy import select, func

from app import config
from app.core.database import session_scope
from app.core.response import ok
from app.models.base import EnergyType, EmissionFactor, CarbonQuota
from app.models.statistics import MonthlySummary, AlertRecord
from app.models.business import (CarbonEmission, Production, ProductFootprint,
                                 SupplyChainCarbon, ComplianceRecord, CarbonBudget)
from app.models.collection import MeterPoint, MeterReading, ManualReport
from app.services import carbon_calc, footprint as footprint_svc, forecast

router = APIRouter(tags=["碳管理"])


def _energy_map():
    with session_scope("base") as s:
        rows = s.scalars(select(EnergyType)).all()
    return {r.code: {"name": r.name, "unit": r.unit} for r in rows}


def _factor_map():
    with session_scope("base") as s:
        rows = s.scalars(select(EmissionFactor)).all()
    return {r.energy_code: r.factor for r in rows}


def _latest_month():
    with session_scope("statistics") as s:
        row = s.execute(select(MonthlySummary.period).order_by(MonthlySummary.period.desc())).first()
    return row[0] if row else None


def _ytd_keys(anchor):
    return [f"{anchor[:4]}-{m:02d}" for m in range(1, int(anchor[5:7]) + 1)]


def _last12_keys(anchor):
    from app.services.energy_calc import shift_month
    return [shift_month(anchor, -i) for i in range(11, -1, -1)]


# ---------- 7 预算管理 ----------
@router.get("/carbon/budget")
def carbon_budget():
    anchor = _latest_month()
    if not anchor:
        def empty_section(name):
            return {"type": name, "budget": 0.0, "actual": 0.0, "rate": 0.0,
                    "time_progress": 0.0, "forecast_year_end": 0.0, "status": "无数据"}
        return ok({"year": None, "period_label": None,
                   "energy": empty_section("energy"), "carbon": empty_section("carbon"),
                   "alerts": [], "message": "暂无数据"})
    keys = _ytd_keys(anchor)
    with session_scope("business") as s:
        budget = s.scalars(select(CarbonBudget).order_by(CarbonBudget.year.desc())).first()
        emissions = s.scalars(select(CarbonEmission).where(CarbonEmission.period.in_(keys))).all()
    with session_scope("statistics") as s:
        summaries = s.scalars(select(MonthlySummary).where(MonthlySummary.period.in_(keys))).all()

    year = int(anchor[:4])
    month_n = int(anchor[5:7])
    energy_actual = sum(r.ce_quantity for r in summaries)
    carbon_actual = sum(r.emission for r in emissions)
    energy_budget = budget.energy_budget if budget else 0.0
    carbon_budget = budget.emission_budget if budget else 0.0

    # 月度序列 → 预测全年
    with session_scope("statistics") as s:
        all_months = s.execute(
            select(MonthlySummary.period, MonthlySummary.ce_quantity).where(
                MonthlySummary.period.like(f"{year}%"))).all()
    ce_series, co2_series = [], []
    monthly_ce = {}
    for row in all_months:
        monthly_ce[row.period] = monthly_ce.get(row.period, 0.0) + row.ce_quantity
    ce_series = [monthly_ce.get(f"{year}-{m:02d}", 0.0) for m in range(1, month_n + 1)]
    with session_scope("business") as s:
        em_rows = s.scalars(select(CarbonEmission).where(CarbonEmission.period.like(f"{year}%"))).all()
    monthly_co2 = {}
    for r in em_rows:
        monthly_co2[r.period] = monthly_co2.get(r.period, 0.0) + r.emission
    co2_series = [monthly_co2.get(f"{year}-{m:02d}", 0.0) for m in range(1, month_n + 1)]

    remain = 12 - month_n
    energy_forecast = energy_actual + forecast.forecast_total(ce_series, remain)
    carbon_forecast = carbon_actual + forecast.forecast_total(co2_series, remain)

    def section(name, budget_v, actual, forecast_v):
        rate = round(actual / budget_v * 100.0, 1) if budget_v else 0.0
        progress = round(month_n / 12 * 100.0, 1)
        if forecast_v > budget_v:
            status = "超预算预警"
        elif rate > progress * 1.1:
            status = "进度偏快"
        else:
            status = "正常"
        return {"type": name, "budget": round(budget_v, 1), "actual": round(actual, 1),
                "rate": rate, "time_progress": progress, "forecast_year_end": round(forecast_v, 1),
                "status": status}

    alerts = []
    if carbon_forecast > carbon_budget:
        alerts.append({"level": "critical",
                       "message": f"全年碳排放预测 {round(carbon_forecast, 0)} tCO2 超出预算 {carbon_budget} tCO2"})
    if energy_forecast > energy_budget:
        alerts.append({"level": "warning",
                       "message": f"全年用能预测 {round(energy_forecast, 0)} tce 超出预算 {energy_budget} tce"})

    return ok({
        "year": year,
        "period_label": f"{year}年1-{month_n}月",
        "energy": section("energy", energy_budget, energy_actual, energy_forecast),
        "carbon": section("carbon", carbon_budget, carbon_actual, carbon_forecast),
        "alerts": alerts,
    })


# ---------- 8 碳排放核算 ----------
@router.get("/carbon/emission")
def carbon_emission():
    anchor = _latest_month()
    if not anchor:
        return ok({"range": [], "total": 0.0, "unit": "tCO2", "intensity": None,
                   "intensity_unit": "tCO2/t产品", "breakdown": [], "trend": [],
                   "alerts": [], "message": "暂无数据"})
    keys = _last12_keys(anchor)
    with session_scope("business") as s:
        rows = s.scalars(select(CarbonEmission).where(CarbonEmission.period.in_(keys))).all()
        output_rows = s.scalars(select(Production).where(Production.period.in_(keys))).all()
        budget = s.scalars(select(CarbonBudget).order_by(CarbonBudget.year.desc())).first()
    emap = _energy_map()

    by_energy, monthly = {}, {}
    for r in rows:
        by_energy[r.energy_code] = by_energy.get(r.energy_code, 0.0) + r.emission
        monthly[r.period] = monthly.get(r.period, 0.0) + r.emission
    total, breakdown = carbon_calc.breakdown(by_energy, {c: v["name"] for c, v in emap.items()})
    total_output = sum(p.output for p in output_rows)
    trend = [{"period": k, "emission": round(monthly.get(k, 0.0), 2)} for k in keys]

    monthly_budget = budget.emission_budget / 12 if budget else 0.0
    alerts = carbon_calc.monthly_overrun_alerts(trend, monthly_budget)

    return ok({
        "range": [keys[0], keys[-1]],
        "total": total,
        "unit": "tCO2",
        "intensity": carbon_calc.carbon_intensity(total, total_output),
        "intensity_unit": "tCO2/t产品",
        "breakdown": breakdown,
        "trend": trend,
        "alerts": alerts,
    })


# ---------- 9 产品碳足迹 ----------
@router.get("/carbon/footprint")
def carbon_footprint(product: str = Query(None)):
    product_label = product or "全部产品"
    with session_scope("business") as s:
        stmt = select(ProductFootprint)
        if product:
            stmt = stmt.where(ProductFootprint.product == product)
        records = s.scalars(stmt).all()
    records = [{"stage": r.stage, "emission": r.emission, "output": r.output,
                "period": r.period, "product": r.product} for r in records]
    if not records:
        return ok({"product": product_label, "stages": [], "total_emission": 0})

    total, stages = footprint_svc.stage_summary(records)
    # 产量：按期间去重求和
    outputs = {}
    for r in records:
        outputs[r["period"]] = max(outputs.get(r["period"], 0.0), r["output"])
    total_output = sum(outputs.values())
    unit = footprint_svc.unit_footprint(total, total_output)

    return ok({
        "product": product_label,
        "standard": "GB/T 24067",
        "range": [min(outputs), max(outputs)] if outputs else [],
        "stages": stages,
        "total_emission": total,
        "total_output": round(total_output, 1),
        "unit_footprint": unit,
        "unit_footprint_unit": "kgCO2e/t",
        "label": footprint_svc.carbon_label(unit),
    })


# ---------- 10 供应链碳管理 ----------
@router.get("/carbon/supply-chain")
def supply_chain():
    with session_scope("business") as s:
        rows = s.scalars(select(SupplyChainCarbon)).all()
    items = [{
        "company": r.company,
        "direction": "上游" if r.direction == "upstream" else "下游",
        "link": r.link,
        "product": r.product,
        "emission": round(r.emission, 1),
        "data_status": r.data_status,
        "period": r.period,
    } for r in rows]
    upstream = sum(i["emission"] for i in items if i["direction"] == "上游")
    downstream = sum(i["emission"] for i in items if i["direction"] == "下游")
    return ok({
        "items": items,
        "summary": {
            "upstream_total": round(upstream, 1),
            "downstream_total": round(downstream, 1),
            "verified_count": sum(1 for i in items if i["data_status"] == "verified"),
            "total": len(items),
        },
    })


# ---------- 11/12 碳核查支撑 ----------
def _empty_audit_context():
    return {
        "period_label": None,
        "total_emission": 0.0,
        "items": [],
        "standards": config.STANDARDS,
        "data_basis": {"meter_readings": 0, "manual_reports": 0, "methods": []},
        "message": "暂无数据",
    }


def _audit_context():
    anchor = _latest_month()
    if not anchor:
        return None
    keys = _ytd_keys(anchor)
    emap = _energy_map()
    fmap = _factor_map()

    with session_scope("business") as s:
        rows = s.scalars(select(CarbonEmission).where(CarbonEmission.period.in_(keys))).all()
    quantity_by_energy, emission_by_energy = {}, {}
    for r in rows:
        quantity_by_energy[r.energy_code] = quantity_by_energy.get(r.energy_code, 0.0) + r.quantity
        emission_by_energy[r.energy_code] = emission_by_energy.get(r.energy_code, 0.0) + r.emission

    # 每能源主导采集方式（按计量点数量）；计数用 COUNT(*)，禁止全量加载
    with session_scope("collection") as s:
        points = s.scalars(select(MeterPoint)).all()
        reading_count = s.execute(select(func.count(MeterReading.id))).scalar()
        manual_count = s.execute(select(func.count(ManualReport.id))).scalar()
    method_by_energy = {}
    for p in points:
        method_by_energy.setdefault(p.energy_code, p.collect_method)
    methods = sorted({p.collect_method for p in points})

    items = []
    for code in quantity_by_energy:
        items.append({
            "energy_code": code,
            "energy_name": emap.get(code, {}).get("name", code),
            "unit": emap.get(code, {}).get("unit", ""),
            "quantity": quantity_by_energy[code],
            "factor": fmap.get(code, 0.0),
            "emission": emission_by_energy[code],
            "collect_method": method_by_energy.get(code, "系统对接"),
            "source": "GB/T 32151",
            "period_label": f"{keys[0]} ~ {keys[-1]}",
        })
    items.sort(key=lambda i: i["emission"], reverse=True)

    context = {
        "period_label": f"{keys[0]} ~ {keys[-1]}",
        "total_emission": round(sum(emission_by_energy.values()), 2),
        "items": items,
        "standards": config.STANDARDS,
        "data_basis": {
            "meter_readings": reading_count,
            "manual_reports": manual_count,
            "methods": methods,
        },
    }
    return context


@router.get("/carbon/audit")
def carbon_audit():
    context = _audit_context() or _empty_audit_context()
    with session_scope("statistics") as s:
        alerts = s.scalars(select(AlertRecord).order_by(AlertRecord.created_at.desc()).limit(10)).all()
    return ok({
        **context,
        "recent_alerts": [{"type": a.alert_type, "level": a.level, "message": a.message} for a in alerts],
    })


@router.get("/carbon/audit/export")
def carbon_audit_export():
    from app.services import report_export
    context = _audit_context() or _empty_audit_context()
    csv_bytes = report_export.build_audit_csv(context["items"])
    year_tag = context["period_label"][:4] if context.get("period_label") else "unknown"
    filename = f"carbon_audit_{year_tag}.csv"
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}',
        },
    )


@router.get("/carbon/audit/report")
def carbon_audit_report():
    """碳核查报告文本：带 UTF-8 BOM 的 text/plain 附件。"""
    from app.services import report_export
    context = _audit_context() or _empty_audit_context()
    text = report_export.build_audit_report(context)
    content = ("\ufeff" + text).encode("utf-8")
    filename = "carbon_audit_report.txt"
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}',
        },
    )


# ---------- 13 碳资产管理 ----------
@router.get("/carbon/asset")
def carbon_asset():
    anchor = _latest_month()
    if not anchor:
        return ok({"year": None, "quota": 0.0, "actual": 0.0, "surplus": 0.0,
                   "usage_rate": 0.0, "forecast_year_end": 0.0,
                   "compliance_deadline": None, "status": "无数据",
                   "alerts": [], "history": [], "message": "暂无数据"})
    year = int(anchor[:4])
    keys = _ytd_keys(anchor)
    month_n = int(anchor[5:7])

    with session_scope("base") as s:
        quota = s.scalars(select(CarbonQuota).where(CarbonQuota.year == year)).first()
    with session_scope("business") as s:
        rows = s.scalars(select(CarbonEmission).where(CarbonEmission.period.in_(keys))).all()
        history = s.scalars(select(ComplianceRecord).order_by(ComplianceRecord.year.desc())).all()
        em_rows = s.scalars(select(CarbonEmission).where(CarbonEmission.period.like(f"{year}%"))).all()

    allocated = quota.allocated if quota else 0.0
    actual = sum(r.emission for r in rows)
    surplus = allocated - actual

    monthly = {}
    for r in em_rows:
        monthly[r.period] = monthly.get(r.period, 0.0) + r.emission
    series = [monthly.get(f"{year}-{m:02d}", 0.0) for m in range(1, month_n + 1)]
    forecast_total = actual + forecast.forecast_total(series, 12 - month_n)

    alerts = []
    if forecast_total > allocated:
        status = "预计超配额"
        alerts.append({"level": "critical",
                       "message": f"全年排放预测 {round(forecast_total, 0)} tCO2 超出配额 {allocated} tCO2，建议启动配额采购"})
    elif surplus < allocated * 0.1:
        status = "盈余偏紧"
        alerts.append({"level": "warning", "message": "配额盈余不足 10%，建议关注后续排放走势"})
    else:
        status = "盈余充足"

    return ok({
        "year": year,
        "quota": round(allocated, 1),
        "actual": round(actual, 1),
        "surplus": round(surplus, 1),
        "usage_rate": round(actual / allocated * 100.0, 1) if allocated else 0.0,
        "forecast_year_end": round(forecast_total, 1),
        "compliance_deadline": f"{year}-12-31",
        "status": status,
        "alerts": alerts,
        "history": [{
            "year": h.year, "quota": h.quota, "actual_emission": h.actual_emission,
            "surplus": h.surplus, "status": h.status,
        } for h in history],
    })
