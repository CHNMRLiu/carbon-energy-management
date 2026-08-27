# -*- coding: utf-8 -*-
"""大屏汇总 API：KPI、实时功率、碳排月度趋势。"""
from fastapi import APIRouter
from sqlalchemy import select

from app.core.database import session_scope
from app.core.response import ok
from app.models.base import CarbonQuota
from app.models.statistics import MonthlySummary
from app.models.business import CarbonEmission
from app.models.collection import MeterPoint, MeterReading

router = APIRouter(tags=["大屏"])


def _latest_month():
    with session_scope("statistics") as s:
        row = s.execute(select(MonthlySummary.period).order_by(MonthlySummary.period.desc())).first()
    return row[0] if row else None


def _realtime_power():
    """电力「仪表采集」点最新读数求和（kW）。"""
    with session_scope("collection") as s:
        points = s.scalars(
            select(MeterPoint).where(
                MeterPoint.energy_code == "electricity",
                MeterPoint.collect_method == "仪表采集",
            )).all()
        total, latest_ts = 0.0, None
        for p in points:
            row = s.scalars(
                select(MeterReading).where(MeterReading.point_id == p.id)
                .order_by(MeterReading.ts.desc()).limit(1)).first()
            if row:
                total += row.value
                if latest_ts is None or row.ts > latest_ts:
                    latest_ts = row.ts
    return round(total, 1), latest_ts.strftime("%Y-%m-%d %H:%M:%S") if latest_ts else None


@router.get("/overview")
def overview():
    anchor = _latest_month()
    power_kw, power_ts = _realtime_power()
    if not anchor:
        return ok({
            "period": None,
            "kpi": {
                "comprehensive_energy": {"value": 0.0, "unit": "tce"},
                "carbon_emission": {"value": 0.0, "unit": "tCO2"},
                "realtime_power": {"value": power_kw, "unit": "kW"},
                "quota_surplus": {"value": 0.0, "unit": "tCO2"},
            },
            "realtime_power": {"value": power_kw, "unit": "kW", "updated_at": power_ts},
            "carbon_trend": [],
            "message": "暂无统计数据",
        })
    year = int(anchor[:4])
    keys = [f"{year}-{m:02d}" for m in range(1, int(anchor[5:7]) + 1)]

    with session_scope("statistics") as s:
        summaries = s.scalars(select(MonthlySummary).where(MonthlySummary.period.in_(keys))).all()
    with session_scope("business") as s:
        emissions = s.scalars(select(CarbonEmission).where(CarbonEmission.period.in_(keys))).all()
    with session_scope("base") as s:
        quota = s.scalars(select(CarbonQuota).where(CarbonQuota.year == year)).first()

    total_tce = sum(r.ce_quantity for r in summaries)
    total_co2 = sum(r.emission for r in emissions)
    allocated = quota.allocated if quota else 0.0

    # 近 12 个月碳排趋势
    from app.services.energy_calc import shift_month
    trend_keys = [shift_month(anchor, -i) for i in range(11, -1, -1)]
    with session_scope("business") as s:
        trend_rows = s.scalars(select(CarbonEmission).where(CarbonEmission.period.in_(trend_keys))).all()
    monthly = {}
    for r in trend_rows:
        monthly[r.period] = monthly.get(r.period, 0.0) + r.emission

    return ok({
        "period": f"{year}年1-{int(anchor[5:7])}月",
        "kpi": {
            "comprehensive_energy": {"value": round(total_tce, 1), "unit": "tce"},
            "carbon_emission": {"value": round(total_co2, 1), "unit": "tCO2"},
            "realtime_power": {"value": power_kw, "unit": "kW"},
            "quota_surplus": {"value": round(allocated - total_co2, 1), "unit": "tCO2"},
        },
        "realtime_power": {"value": power_kw, "unit": "kW", "updated_at": power_ts},
        "carbon_trend": [{"period": k, "emission": round(monthly.get(k, 0.0), 1)} for k in trend_keys],
    })
