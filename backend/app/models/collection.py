# -*- coding: utf-8 -*-
"""collection.db ORM：计量点台账、采集原始记录、手工填报单。"""
from datetime import datetime

from sqlalchemy import String, Float, Integer, DateTime, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class MeterPoint(Base):
    """计量点台账（覆盖 系统对接/仪表采集/手工填报/烟感实测 四种采集方式）。"""
    __tablename__ = "meter_point"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64))
    energy_code: Mapped[str] = mapped_column(String(32))
    org_code: Mapped[str] = mapped_column(String(32), default="")
    collect_method: Mapped[str] = mapped_column(String(16), index=True)  # 四种采集方式
    unit: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="normal")
    rated_value: Mapped[float] = mapped_column(Float, default=0.0)  # 模拟器典型负荷


class MeterReading(Base):
    """采集原始记录（仪表/系统对接/烟感均落入此表）。"""
    __tablename__ = "meter_reading"
    __table_args__ = (Index("ix_meter_reading_point_ts", "point_id", "ts"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    point_id: Mapped[int] = mapped_column(Integer, index=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True)
    value: Mapped[float] = mapped_column(Float)
    quality: Mapped[str] = mapped_column(String(16), default="good")   # good/suspect/bad
    source: Mapped[str] = mapped_column(String(16), default="meter")   # meter/external/smoke/simulator


class ManualReport(Base):
    """手工填报单。"""
    __tablename__ = "manual_report"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    point_code: Mapped[str] = mapped_column(String(32), index=True)
    org_code: Mapped[str] = mapped_column(String(32), default="")
    energy_code: Mapped[str] = mapped_column(String(32), default="")
    period: Mapped[str] = mapped_column(String(16))            # YYYY-MM
    value: Mapped[float] = mapped_column(Float)
    reporter: Mapped[str] = mapped_column(String(32), default="")
    reported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    remark: Mapped[str] = mapped_column(String(128), default="")
