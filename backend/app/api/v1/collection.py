# -*- coding: utf-8 -*-
"""数据采集层 API：仪表上报(202)/手工填报/系统对接/烟感实测/计量点列表。"""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app import config
from app.core.database import session_scope
from app.core.response import ok, fail
from app.models.collection import MeterPoint, MeterReading, ManualReport
from app.schemas.ingest import MeterReadingIn, ManualReportIn

router = APIRouter(prefix="/ingest", tags=["数据采集"])


def _point_index():
    with session_scope("collection") as s:
        rows = s.scalars(select(MeterPoint)).all()
    return {p.id: p for p in rows}, {p.code: p for p in rows}


def _enqueue(request: Request, records: List[MeterReadingIn], source: str):
    """把上报数据规范化后塞入进程内队列；返回 (accepted, rejected)。"""
    queue = request.app.state.queue
    by_id, by_code = _point_index()
    accepted = rejected = 0
    now = datetime.now()
    for rec in records:
        point = None
        if rec.point_id is not None:
            point = by_id.get(rec.point_id)
        elif rec.point_code:
            point = by_code.get(rec.point_code)
        if point is None:
            rejected += 1
            continue
        try:
            queue.put_nowait({
                "point_id": point.id,
                "ts": rec.ts or now,
                "value": rec.value,
                "quality": rec.quality,
                "source": source,
            })
            accepted += 1
        except Exception:
            rejected += 1
    return accepted, rejected


@router.post("/meter")
async def ingest_meter(request: Request, records: List[MeterReadingIn]):
    """仪表批量上报：≤1000 条，入队后立即返回 202，后台任务批量落库。"""
    if len(records) > config.INGEST_BATCH_LIMIT:
        return JSONResponse(
            status_code=400,
            content=fail(40013, f"单次上报不得超过 {config.INGEST_BATCH_LIMIT} 条"),
        )
    accepted, rejected = _enqueue(request, records, "meter")
    return JSONResponse(
        status_code=202,
        content=ok({"accepted": accepted, "rejected": rejected, "queued": True}),
    )


@router.post("/external")
async def ingest_external(request: Request, records: List[MeterReadingIn]):
    """系统对接：管理信息系统/生产监控系统接口调用上报。"""
    if len(records) > config.INGEST_BATCH_LIMIT:
        return JSONResponse(status_code=400, content=fail(40013, "单次上报不得超过 1000 条"))
    accepted, rejected = _enqueue(request, records, "external")
    return JSONResponse(
        status_code=202,
        content=ok({"accepted": accepted, "rejected": rejected, "queued": True}),
    )


@router.post("/smoke")
async def ingest_smoke(request: Request, records: List[MeterReadingIn]):
    """烟感实测：在线监测集中排放场景。"""
    if len(records) > config.INGEST_BATCH_LIMIT:
        return JSONResponse(status_code=400, content=fail(40013, "单次上报不得超过 1000 条"))
    accepted, rejected = _enqueue(request, records, "smoke")
    return JSONResponse(
        status_code=202,
        content=ok({"accepted": accepted, "rejected": rejected, "queued": True}),
    )


@router.post("/manual")
def ingest_manual(payload: ManualReportIn):
    """手工填报：写入填报单；若计量点存在则同步生成一条采集记录。"""
    with session_scope("collection") as s:
        point = s.scalars(select(MeterPoint).where(MeterPoint.code == payload.point_code)).first()
        report = ManualReport(
            point_code=payload.point_code,
            org_code=point.org_code if point else "",
            energy_code=point.energy_code if point else "",
            period=payload.period,
            value=payload.value,
            reporter=payload.reporter,
            reported_at=datetime.now(),
            remark=payload.remark,
        )
        s.add(report)
        s.flush()
        report_id = report.id
        # 闭环：计量点存在时同步生成一条采集记录
        reading_id = None
        if point is not None:
            reading = MeterReading(point_id=point.id, ts=datetime.now(),
                                   value=payload.value, quality="good", source="manual")
            s.add(reading)
            s.flush()
            reading_id = reading.id
    return ok({"id": report_id, "reading_id": reading_id,
               "point_code": payload.point_code, "period": payload.period})


@router.get("/points")
def list_points(collect_method: str = None):
    """计量点列表（可按采集方式过滤）。"""
    with session_scope("collection") as s:
        stmt = select(MeterPoint)
        if collect_method:
            stmt = stmt.where(MeterPoint.collect_method == collect_method)
        rows = s.scalars(stmt).all()
    return ok({
        "total": len(rows),
        "methods": list(config.COLLECT_METHODS),
        "items": [{
            "id": p.id, "code": p.code, "name": p.name, "energy_code": p.energy_code,
            "org_code": p.org_code, "collect_method": p.collect_method,
            "unit": p.unit, "status": p.status,
        } for p in rows],
    })
