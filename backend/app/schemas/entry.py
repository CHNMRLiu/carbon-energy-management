# -*- coding: utf-8 -*-
"""12 项业务功能手工录入 Pydantic v2 DTO。"""
from typing import Optional

from pydantic import BaseModel, Field

_PERIOD_RE = r"^\d{4}-(0[1-9]|1[0-2])$"


class ConsumptionEntryIn(BaseModel):
    """1 能耗查询：能耗账单/月读数。"""
    energy_code: str = Field(..., description="能源编码，如 electricity/coal")
    workshop: str = Field("", description="车间编码或名称，如 ws1/一车间，留空记为全厂")
    period: str = Field(..., pattern=_PERIOD_RE, description="YYYY-MM")
    amount: float = Field(..., ge=0, description="实物量")
    cost: Optional[float] = Field(None, ge=0, description="成本（元），缺省按字典单价计算")


class ProductionEntryIn(BaseModel):
    """2 能耗计算：产量产值。"""
    period: str = Field(..., pattern=_PERIOD_RE, description="YYYY-MM")
    product: Optional[str] = Field(None, description="产品名称，缺省为综合")
    quantity: float = Field(..., ge=0, description="产量 t")
    output_value_wan: float = Field(..., ge=0, description="产值（万元）")


class EnergyPriceIn(BaseModel):
    """3 分析与策略：能源单价。"""
    energy_code: str
    price: float = Field(..., ge=0, description="元/物理量单位")
    period: Optional[str] = Field(None, description="生效期间（可选，仅备注用途）")


class BenchmarkEntryIn(BaseModel):
    """4 能效对标：对标项实际值。"""
    category: str = Field(..., pattern=r"^(process|product|device|equipment)$")
    name: str = Field(..., min_length=1)
    actual_value: float = Field(..., ge=0)
    limit_value: Optional[float] = Field(None, ge=0)


class FlowLossIn(BaseModel):
    """5 能流分析：转换/分配损耗率。"""
    stage: str = Field(..., min_length=1, description="global 或车间名（一车间/二车间/三车间）")
    loss_rate: float = Field(..., ge=0, le=1)


class OptimizationEntryIn(BaseModel):
    """6 能效优化：设备运行参数。"""
    device: str = Field(..., min_length=1, description="设备编码（EQ+序号）或名称")
    param: str = Field(..., pattern=r"^(efficiency|rated_power|standard_value)$")
    value: float = Field(..., ge=0)


class BudgetEntryIn(BaseModel):
    """7 碳预算：年度预算。"""
    year: int = Field(..., ge=2000, le=2100)
    energy_budget_tce: float = Field(..., ge=0)
    carbon_budget_tco2: float = Field(..., ge=0)


class EmissionFactorIn(BaseModel):
    """8 碳排放核算：排放因子。"""
    energy_code: str
    factor: float = Field(..., ge=0, description="tCO2/物理量单位")


class FootprintEntryIn(BaseModel):
    """9 产品碳足迹：阶段排放。"""
    product: str = Field(..., min_length=1)
    stage: str = Field(..., pattern=r"^(raw_material|production|transport|use|recycle)$")
    emission: float = Field(..., ge=0, description="tCO2")
    period: Optional[str] = Field(None, pattern=_PERIOD_RE)


class SupplyChainEntryIn(BaseModel):
    """10 供应链碳：链上企业数据。"""
    company: str = Field(..., min_length=1)
    direction: str = Field(..., pattern=r"^(upstream|downstream|上游|下游)$")
    scope: str = Field("", description="业务环节")
    emission: float = Field(..., ge=0, description="tCO2")
    status: Optional[str] = Field(None, pattern=r"^(verified|reported|pending)$")


class AuditMaterialIn(BaseModel):
    """11 碳核查：补充材料。"""
    name: str = Field(..., min_length=1)
    type: str = Field("其他")
    remark: str = ""


class QuotaEntryIn(BaseModel):
    """12 碳资产：配额调整。"""
    year: int = Field(..., ge=2000, le=2100)
    quota: float = Field(..., ge=0, description="tCO2")
    remark: str = ""
