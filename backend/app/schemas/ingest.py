# -*- coding: utf-8 -*-
"""采集层 Pydantic v2 DTO。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MeterReadingIn(BaseModel):
    """仪表/系统对接/烟感 单条上报。"""
    point_id: Optional[int] = None
    point_code: Optional[str] = None
    ts: Optional[datetime] = None
    value: float = Field(ge=0)
    quality: str = "good"


class ManualReportIn(BaseModel):
    """手工填报单。"""
    point_code: str
    period: str = Field(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="YYYY-MM")
    value: float = Field(ge=0)
    reporter: str = "手工填报员"
    remark: str = ""


class IngestAck(BaseModel):
    accepted: int
    rejected: int = 0
    queued: bool = True
