# -*- coding: utf-8 -*-
"""statistics.db ORM：月/年汇总、对标结果、预算执行、预警记录。"""
from datetime import datetime

from sqlalchemy import String, Float, Integer, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class MonthlySummary(Base):
    """月度汇总表（组织×能源×月）。"""
    __tablename__ = "monthly_summary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_code: Mapped[str] = mapped_column(String(32), index=True)
    energy_code: Mapped[str] = mapped_column(String(32), index=True)
    period: Mapped[str] = mapped_column(String(16), index=True)     # YYYY-MM
    quantity: Mapped[float] = mapped_column(Float)                  # 物理量
    ce_quantity: Mapped[float] = mapped_column(Float)               # tce
    cost: Mapped[float] = mapped_column(Float)                      # 元


class YearlySummary(Base):
    """年度汇总表。"""
    __tablename__ = "yearly_summary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_code: Mapped[str] = mapped_column(String(32), index=True)
    energy_code: Mapped[str] = mapped_column(String(32), index=True)
    period: Mapped[str] = mapped_column(String(16), index=True)     # YYYY
    quantity: Mapped[float] = mapped_column(Float)
    ce_quantity: Mapped[float] = mapped_column(Float)
    cost: Mapped[float] = mapped_column(Float)


class BenchmarkResult(Base):
    """对标结果。"""
    __tablename__ = "benchmark_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period: Mapped[str] = mapped_column(String(16), index=True)
    category: Mapped[str] = mapped_column(String(16))               # process/product/equipment
    item_code: Mapped[str] = mapped_column(String(32))
    item_name: Mapped[str] = mapped_column(String(64))
    actual_value: Mapped[float] = mapped_column(Float)
    limit_value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(32))
    achieved: Mapped[bool] = mapped_column(Boolean, default=True)


class BudgetExecution(Base):
    """预算执行。"""
    __tablename__ = "budget_execution"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period: Mapped[str] = mapped_column(String(16), index=True)
    budget_type: Mapped[str] = mapped_column(String(16))            # energy/carbon
    budget_value: Mapped[float] = mapped_column(Float)
    actual_value: Mapped[float] = mapped_column(Float)
    rate: Mapped[float] = mapped_column(Float)                      # %


class AlertRecord(Base):
    """预警记录。"""
    __tablename__ = "alert_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    alert_type: Mapped[str] = mapped_column(String(32))             # carbon/budget/benchmark/quota
    level: Mapped[str] = mapped_column(String(16))                  # info/warning/critical
    message: Mapped[str] = mapped_column(String(256))
