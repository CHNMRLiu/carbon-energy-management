# -*- coding: utf-8 -*-
"""business.db ORM：能耗账单、产量产值、碳核算、产品碳足迹、供应链、履约、碳预算。"""
from datetime import datetime

from sqlalchemy import String, Float, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class EnergyBill(Base):
    """能耗账单。"""
    __tablename__ = "energy_bill"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_code: Mapped[str] = mapped_column(String(32), index=True)
    energy_code: Mapped[str] = mapped_column(String(32), index=True)
    period: Mapped[str] = mapped_column(String(16), index=True)     # YYYY-MM
    quantity: Mapped[float] = mapped_column(Float)                  # 物理量
    ce_quantity: Mapped[float] = mapped_column(Float)               # 折标煤 tce
    cost: Mapped[float] = mapped_column(Float)                      # 元


class Production(Base):
    """产品产量与产值。"""
    __tablename__ = "production"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_code: Mapped[str] = mapped_column(String(32), index=True)
    period: Mapped[str] = mapped_column(String(16), index=True)
    product: Mapped[str] = mapped_column(String(64))
    output: Mapped[float] = mapped_column(Float)                    # 产量 t
    output_value: Mapped[float] = mapped_column(Float)              # 产值 万元


class CarbonEmission(Base):
    """碳排放核算结果（按 组织×能源×月度）。"""
    __tablename__ = "carbon_emission"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_code: Mapped[str] = mapped_column(String(32), index=True)
    energy_code: Mapped[str] = mapped_column(String(32), index=True)
    period: Mapped[str] = mapped_column(String(16), index=True)
    quantity: Mapped[float] = mapped_column(Float)                  # 活动水平
    emission: Mapped[float] = mapped_column(Float)                  # tCO2


class ProductFootprint(Base):
    """产品碳足迹记录（生命周期阶段）。"""
    __tablename__ = "product_footprint"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product: Mapped[str] = mapped_column(String(64), index=True)
    period: Mapped[str] = mapped_column(String(16), index=True)
    stage: Mapped[str] = mapped_column(String(32))                  # raw_material/production/transport/use/recycle
    emission: Mapped[float] = mapped_column(Float)                  # tCO2
    output: Mapped[float] = mapped_column(Float)                    # 当期产量 t


class SupplyChainCarbon(Base):
    """供应链碳数据。"""
    __tablename__ = "supply_chain_carbon"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company: Mapped[str] = mapped_column(String(64))
    direction: Mapped[str] = mapped_column(String(16))              # upstream/downstream
    link: Mapped[str] = mapped_column(String(64))                   # 环节
    product: Mapped[str] = mapped_column(String(64), default="")
    emission: Mapped[float] = mapped_column(Float)                  # tCO2
    data_status: Mapped[str] = mapped_column(String(16), default="reported")  # verified/reported/pending
    period: Mapped[str] = mapped_column(String(16), default="2026")


class ComplianceRecord(Base):
    """履约记录。"""
    __tablename__ = "compliance_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer)
    quota: Mapped[float] = mapped_column(Float)
    actual_emission: Mapped[float] = mapped_column(Float)
    surplus: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(16))                 # 已履约/待履约
    check_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class CarbonBudget(Base):
    """碳预算（含用能预算）。"""
    __tablename__ = "carbon_budget"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    energy_budget: Mapped[float] = mapped_column(Float)             # tce
    emission_budget: Mapped[float] = mapped_column(Float)           # tCO2


class AuditMaterial(Base):
    """碳核查补充材料清单（手工录入维护）。"""
    __tablename__ = "audit_material"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64))
    type: Mapped[str] = mapped_column(String(32), default="其他")
    remark: Mapped[str] = mapped_column(String(256), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
