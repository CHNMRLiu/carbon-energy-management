# -*- coding: utf-8 -*-
"""base.db ORM：能源字典、组织/车间/工序、设备台账、排放因子、限额标准、碳配额。"""
from sqlalchemy import String, Float, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class EnergyType(Base):
    """能源类型字典（GB/T 2589 折标系数）。"""
    __tablename__ = "energy_type"

    code: Mapped[str] = mapped_column(String(32), primary_key=True)          # coal/electricity/...
    name: Mapped[str] = mapped_column(String(32))                            # 煤炭/电力/...
    unit: Mapped[str] = mapped_column(String(16))                            # 物理量单位
    ce_coefficient: Mapped[float] = mapped_column(Float)                     # kgce/单位
    price: Mapped[float] = mapped_column(Float, default=0.0)                 # 元/单位


class Organization(Base):
    """组织：公司 / 车间 / 工序。"""
    __tablename__ = "organization"

    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    level: Mapped[str] = mapped_column(String(16))            # company/workshop/process
    parent_code: Mapped[str] = mapped_column(String(32), default="")


class Equipment(Base):
    """设备台账。"""
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_code: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(64))
    category: Mapped[str] = mapped_column(String(32))         # 电炉/空压机/水泵/风机...
    energy_code: Mapped[str] = mapped_column(String(32), default="electricity")
    rated_power: Mapped[float] = mapped_column(Float, default=0.0)    # kW
    efficiency: Mapped[float] = mapped_column(Float, default=0.0)     # 实测效率 %
    standard_value: Mapped[float] = mapped_column(Float, default=0.0) # 标准效率 %
    install_year: Mapped[int] = mapped_column(Integer, default=2015)


class EmissionFactor(Base):
    """排放因子表（GB/T 32151 系列）。"""
    __tablename__ = "emission_factor"

    energy_code: Mapped[str] = mapped_column(String(32), primary_key=True)
    factor: Mapped[float] = mapped_column(Float)               # tCO2/物理量单位
    standard_source: Mapped[str] = mapped_column(String(64), default="GB/T 32151")


class EnergyLimitStandard(Base):
    """国家单位产品能耗限额标准表。"""
    __tablename__ = "energy_limit_standard"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(16))          # process/product/equipment
    item_code: Mapped[str] = mapped_column(String(32))         # 对应车间/产品/设备编码
    item_name: Mapped[str] = mapped_column(String(64))
    limit_value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(32), default="kgce/t")
    direction: Mapped[str] = mapped_column(String(8), default="le")  # le=越低越好, ge=越高越好


class CarbonQuota(Base):
    """碳配额表。"""
    __tablename__ = "carbon_quota"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    org_code: Mapped[str] = mapped_column(String(32), default="company")
    allocated: Mapped[float] = mapped_column(Float)            # tCO2
    remark: Mapped[str] = mapped_column(String(128), default="")


class FlowLossConfig(Base):
    """能流转换/分配损耗率配置（桑基重算时使用，手工录入维护）。"""
    __tablename__ = "flow_loss_config"

    stage: Mapped[str] = mapped_column(String(32), primary_key=True)   # global/一车间/二车间/三车间...
    loss_rate: Mapped[float] = mapped_column(Float)                    # 0~1
