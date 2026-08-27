# -*- coding: utf-8 -*-
"""seed/generate.py — 固定随机种子的模拟数据生成器。

生成内容：
- 基础库：能源字典(5)/组织(公司+3车间)/工序设备台账/排放因子/限额标准/碳配额
- 采集库：计量点(覆盖4种采集方式) + 近7天小时级抽样明细 + 手工填报单
- 业务库：近24个月账单/产量产值/碳核算/产品碳足迹/供应链/履约/预算
- 统计库：月度与年度汇总、对标结果、预算执行、预警记录
"""
import math
import random
from datetime import datetime, timedelta

from sqlalchemy import select

from app.core.database import session_scope, get_engine

SEED = 20260825
ANCHOR_YEAR, ANCHOR_MONTH = 2026, 8          # 数据截止 2026-08
N_MONTHS = 24                                # 2024-09 ~ 2026-08
PRODUCT = "精密铸件"

# 能源字典：折标系数(GB/T 2589)、单价、排放因子(GB/T 32151, tCO2/单位)
ENERGIES = [
    dict(code="coal", name="煤炭", unit="kg", ce=0.7143, price=0.9, factor=0.0019003),
    dict(code="electricity", name="电力", unit="kWh", ce=0.1229, price=0.68, factor=0.000581),
    dict(code="natural_gas", name="天然气", unit="m3", ce=1.33, price=3.2, factor=0.0021622),
    dict(code="heat", name="热力", unit="MJ", ce=0.0341, price=0.045, factor=0.00011),
    dict(code="diesel", name="柴油", unit="kg", ce=1.4571, price=7.5, factor=0.0030959),
]

# 车间：(编码, 名称, 工序名, 能耗规模系数, 月基准产量 t)
WORKSHOPS = [
    ("ws1", "一车间", "熔炼工序", 1.00, 5200),
    ("ws2", "二车间", "轧制工序", 0.85, 4600),
    ("ws3", "三车间", "精整工序", 0.60, 3800),
]

# 车间×能源 月基准实物量
BASE_QUANTITY = {
    "ws1": {"coal": 150000, "electricity": 420000, "natural_gas": 30000, "heat": 600000, "diesel": 4000},
    "ws2": {"coal": 90000, "electricity": 380000, "natural_gas": 42000, "heat": 420000, "diesel": 3200},
    "ws3": {"coal": 42000, "electricity": 260000, "natural_gas": 21000, "heat": 300000, "diesel": 2200},
}

LIMIT_STANDARDS = [
    ("product", "P001", f"{PRODUCT}单位产品综合能耗", 45.0, "kgce/t", "le"),
    ("process", "ws1", "熔炼工序单位产品能耗", 46.0, "kgce/t", "le"),
    ("process", "ws2", "轧制工序单位产品能耗", 40.0, "kgce/t", "le"),
    ("process", "ws3", "精整工序单位产品能耗", 35.0, "kgce/t", "le"),
]

# 设备台账：(车间, 名称, 类别, 额定功率kW, 实测效率%, 标准效率%, 投运年份)
EQUIPMENTS = [
    ("ws1", "1#电弧炉", "电炉", 2200, 82.0, 86.0, 2014),
    ("ws1", "熔炼除尘风机", "风机", 630, 88.5, 92.0, 2016),
    ("ws1", "1#空压机", "空压机", 450, 89.0, 93.0, 2015),
    ("ws2", "轧机主传动", "风机", 1250, 93.5, 92.0, 2019),
    ("ws2", "2#空压机", "空压机", 355, 90.0, 93.0, 2017),
    ("ws2", "加热炉循环泵", "水泵", 280, 87.0, 92.0, 2016),
    ("ws3", "精整行车", "水泵", 320, 92.5, 92.0, 2020),
    ("ws3", "3#空压机", "空压机", 250, 91.0, 93.0, 2018),
    ("ws3", "退火炉", "加热炉", 800, 84.0, 88.0, 2015),
]

# 计量点：(编码, 名称, 能源, 车间, 采集方式, 单位, 额定负荷)
METER_POINTS = [
    ("EP001", "煤场皮带秤", "coal", "ws1", "系统对接", "kg/h", 25000),
    ("EP002", "天然气总管流量计", "natural_gas", "", "系统对接", "m3/h", 180),
    ("EP010", "全厂总进线电表", "electricity", "", "仪表采集", "kW", 8200),
    ("EP011", "一车间进线电表", "electricity", "ws1", "仪表采集", "kW", 2700),
    ("EP012", "二车间进线电表", "electricity", "ws2", "仪表采集", "kW", 2300),
    ("EP013", "三车间进线电表", "electricity", "ws3", "仪表采集", "kW", 1500),
    ("EP014", "1#电弧炉电表", "electricity", "ws1", "仪表采集", "kW", 1900),
    ("EP015", "空压站总表", "electricity", "ws2", "仪表采集", "kW", 860),
    ("EP020", "柴油储罐库存填报", "diesel", "", "手工填报", "kg", 0),
    ("EP021", "外购热力结算填报", "heat", "", "手工填报", "MJ", 0),
    ("EP030", "烟囱CEMS在线监测", "electricity", "", "烟感实测", "kg/h", 900),
]

STAGE_SHARES = {"raw_material": 0.42, "production": 0.31, "transport": 0.07, "use": 0.14, "recycle": 0.06}


def month_keys():
    keys = []
    y, m = ANCHOR_YEAR, ANCHOR_MONTH
    for _ in range(N_MONTHS):
        keys.append(f"{y}-{m:02d}")
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    return list(reversed(keys))


def _season_factor(period: str, energy_code: str) -> float:
    m = int(period[5:7])
    if energy_code == "electricity":
        return 1 + 0.12 * math.cos(2 * math.pi * (m - 7) / 12) + 0.08 * math.cos(2 * math.pi * (m - 1) / 12)
    if energy_code == "heat":
        return 1 + 0.25 * math.cos(2 * math.pi * (m - 1) / 12)
    return 1 + 0.03 * math.cos(2 * math.pi * (m - 7) / 12)


def _clear(session, models):
    for model in models:
        session.query(model).delete()


def generate(verbose=True):
    from app.models import base as mb, collection as mc, business as mz, statistics as ms

    random.seed(SEED)
    keys = month_keys()
    energy_map = {e["code"]: e for e in ENERGIES}

    # ---------------- base.db ----------------
    with session_scope("base") as s:
        _clear(s, [mb.EnergyType, mb.Organization, mb.Equipment, mb.EmissionFactor,
                   mb.EnergyLimitStandard, mb.CarbonQuota])
        for e in ENERGIES:
            s.add(mb.EnergyType(code=e["code"], name=e["name"], unit=e["unit"],
                                ce_coefficient=e["ce"], price=e["price"]))
            s.add(mb.EmissionFactor(energy_code=e["code"], factor=e["factor"], standard_source="GB/T 32151"))
        s.add(mb.Organization(code="company", name="华东精密制造有限公司", level="company"))
        for code, name, process, _, _ in WORKSHOPS:
            s.add(mb.Organization(code=code, name=name, level="workshop", parent_code="company"))
            s.add(mb.Organization(code=f"{code}_proc", name=process, level="process", parent_code=code))
        for org, name, cat, power, eff, std_eff, year in EQUIPMENTS:
            s.add(mb.Equipment(org_code=org, name=name, category=cat, rated_power=power,
                               efficiency=eff, standard_value=std_eff, install_year=year))
        for cat, code, name, limit_v, unit, direction in LIMIT_STANDARDS:
            s.add(mb.EnergyLimitStandard(category=cat, item_code=code, item_name=name,
                                         limit_value=limit_v, unit=unit, direction=direction))
        s.add(mb.CarbonQuota(year=2025, allocated=27000.0, remark="2025年度免费配额"))
        s.add(mb.CarbonQuota(year=2026, allocated=26000.0, remark="2026年度免费配额（预分配）"))

    # ---------------- 业务/统计：24 个月 ----------------
    monthly_rows, yearly_agg = [], {}
    bills, productions, emissions = [], [], []
    ce_total_by_month, emission_by_month = {}, {}

    for idx, period in enumerate(keys):
        growth = 1 + 0.004 * idx
        for code, name, _, scale, base_output in WORKSHOPS:
            output = round(base_output * growth * random.uniform(0.94, 1.06), 1)
            output_value = round(output * 0.55 * random.uniform(0.97, 1.03), 1)
            productions.append(dict(org_code=code, period=period, product=PRODUCT,
                                    output=output, output_value=output_value))
            for e in ENERGIES:
                qty = BASE_QUANTITY[code][e["code"]] * scale * growth
                qty *= _season_factor(period, e["code"]) * random.uniform(0.94, 1.06)
                qty = round(qty, 1)
                ce = qty * e["ce"] / 1000.0
                cost = round(qty * e["price"], 2)
                emission = qty * e["factor"]
                monthly_rows.append(dict(org_code=code, energy_code=e["code"], period=period,
                                         quantity=qty, ce_quantity=round(ce, 4), cost=cost))
                bills.append(dict(org_code=code, energy_code=e["code"], period=period,
                                  quantity=qty, ce_quantity=round(ce, 4), cost=cost))
                emissions.append(dict(org_code=code, energy_code=e["code"], period=period,
                                      quantity=qty, emission=round(emission, 4)))
                year = period[:4]
                yrow = yearly_agg.setdefault((year, code, e["code"]), [0.0, 0.0, 0.0])
                yrow[0] += qty; yrow[1] += ce; yrow[2] += cost
                ce_total_by_month[period] = ce_total_by_month.get(period, 0.0) + ce
                emission_by_month[period] = emission_by_month.get(period, 0.0) + emission

    with session_scope("statistics") as s:
        _clear(s, [ms.MonthlySummary, ms.YearlySummary])
        s.add_all([ms.MonthlySummary(**r) for r in monthly_rows])
        s.add_all([ms.YearlySummary(org_code=code, energy_code=ec, period=year,
                                    quantity=round(v[0], 1), ce_quantity=round(v[1], 4), cost=round(v[2], 2))
                   for (year, code, ec), v in yearly_agg.items()])

    with session_scope("business") as s:
        _clear(s, [mz.EnergyBill, mz.Production, mz.CarbonEmission, mz.ProductFootprint,
                   mz.SupplyChainCarbon, mz.ComplianceRecord, mz.CarbonBudget])
        s.add_all([mz.EnergyBill(**r) for r in bills])
        s.add_all([mz.Production(**r) for r in productions])
        s.add_all([mz.CarbonEmission(**r) for r in emissions])

        # 产品碳足迹（近12个月，五阶段）
        for period in keys[-12:]:
            month_output = sum(p["output"] for p in productions if p["period"] == period)
            month_emission = emission_by_month.get(period, 0.0) * 0.9
            for stage, share in STAGE_SHARES.items():
                s.add(mz.ProductFootprint(product=PRODUCT, period=period, stage=stage,
                                          emission=round(month_emission * share, 3), output=month_output))

        # 供应链碳数据
        for company, direction, link, product, emission, status in [
            ("宏达矿业", "upstream", "原材料供应-生铁", "生铁", 5200.0, "verified"),
            ("绿源再生资源", "upstream", "原材料供应-废钢", "废钢", 1150.0, "verified"),
            ("中天物流", "upstream", "原料运输", "运输服务", 480.0, "reported"),
            ("蓝天燃气", "upstream", "天然气供应", "天然气", 830.0, "reported"),
            ("精工装备制造", "downstream", "产品使用", PRODUCT, 2600.0, "reported"),
            ("华成机械", "downstream", "产品使用", PRODUCT, 1900.0, "pending"),
            ("循环回收科技", "downstream", "回收处置", "废料回收", 260.0, "verified"),
        ]:
            s.add(mz.SupplyChainCarbon(company=company, direction=direction, link=link, product=product,
                                       emission=emission, data_status=status, period="2026"))

        # 履约记录（2025）
        emission_2025 = sum(v for k, v in emission_by_month.items() if k.startswith("2025"))
        s.add(mz.ComplianceRecord(year=2025, quota=27000.0, actual_emission=round(emission_2025, 1),
                                  surplus=round(27000.0 - emission_2025, 1), status="已履约",
                                  check_time=datetime(2026, 3, 20, 10, 0)))

        # 碳预算（2026）
        tce_2025 = sum(r["ce_quantity"] for r in monthly_rows if r["period"].startswith("2025"))
        s.add(mz.CarbonBudget(year=2026, energy_budget=round(tce_2025 * 1.01, 1), emission_budget=26000.0))

    # ---------------- collection.db ----------------
    with session_scope("collection") as s:
        _clear(s, [mc.MeterPoint, mc.MeterReading, mc.ManualReport])
        for code, name, energy, org, method, unit, rated in METER_POINTS:
            s.add(mc.MeterPoint(code=code, name=name, energy_code=energy, org_code=org,
                                collect_method=method, unit=unit, status="normal", rated_value=rated))
        s.flush()
        points = {p.code: p.id for p in s.scalars(select(mc.MeterPoint)).all()}

        # 仪表类：近7天小时级抽样
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        readings = []
        for code, name, energy, org, method, unit, rated in METER_POINTS:
            if method != "仪表采集":
                continue
            for back in range(7 * 24, -1, -1):
                ts = now - timedelta(hours=back)
                hour = ts.hour
                curve = 0.55 + 0.45 * math.exp(-((hour - 10) ** 2) / 8) + 0.40 * math.exp(-((hour - 15.5) ** 2) / 10)
                readings.append(mc.MeterReading(point_id=points[code], ts=ts,
                                                value=round(rated * min(curve, 1.15) * random.uniform(0.92, 1.08), 2),
                                                quality="good", source="seed"))
        # 烟感点：近1天小时级
        smoke = next((c for c, n, e, o, m, u, r in METER_POINTS if m == "烟感实测"), None)
        if smoke:
            for back in range(24, -1, -1):
                ts = now - timedelta(hours=back)
                readings.append(mc.MeterReading(point_id=points[smoke], ts=ts,
                                                value=round(900 * random.uniform(0.85, 1.1), 1),
                                                quality="good", source="smoke"))
        s.add_all(readings)

        # 手工填报单（近2个月）
        for period in keys[-2:]:
            s.add(mc.ManualReport(point_code="EP020", org_code="", energy_code="diesel", period=period,
                                  value=round(9200 * random.uniform(0.9, 1.1), 1), reporter="仓储科-王工",
                                  reported_at=datetime.now(), remark="月度盘点"))
            s.add(mc.ManualReport(point_code="EP021", org_code="", energy_code="heat", period=period,
                                  value=round(1450000 * random.uniform(0.9, 1.1), 0), reporter="动力科-李工",
                                  reported_at=datetime.now(), remark="供热结算单"))

    # ---------------- statistics.db：对标/预算执行/预警 ----------------
    ytd_keys = [k for k in keys if k.startswith(str(ANCHOR_YEAR))]
    ce_by_org, output_by_org = {}, {}
    for r in monthly_rows:
        if r["period"] in ytd_keys:
            ce_by_org[r["org_code"]] = ce_by_org.get(r["org_code"], 0.0) + r["ce_quantity"] * 1000
    for p in productions:
        if p["period"] in ytd_keys:
            output_by_org[p["org_code"]] = output_by_org.get(p["org_code"], 0.0) + p["output"]
    total_ce = sum(ce_by_org.values())
    total_output = sum(output_by_org.values())

    with session_scope("statistics") as s:
        _clear(s, [ms.BenchmarkResult, ms.BudgetExecution, ms.AlertRecord])
        for cat, code, name, limit_v, unit, direction in LIMIT_STANDARDS:
            if cat == "product":
                actual = total_ce / total_output if total_output else 0
            else:
                actual = ce_by_org.get(code, 0.0) / output_by_org.get(code, 1.0)
            achieved = actual <= limit_v
            s.add(ms.BenchmarkResult(period=f"{ANCHOR_YEAR}-YTD", category=cat, item_code=code,
                                     item_name=name, actual_value=round(actual, 2), limit_value=limit_v,
                                     unit=unit, achieved=achieved))
        for org, name, cat, power, eff, std_eff, year in EQUIPMENTS:
            s.add(ms.BenchmarkResult(period=f"{ANCHOR_YEAR}-YTD", category="equipment", item_code=name,
                                     item_name=name, actual_value=eff, limit_value=std_eff, unit="%",
                                     achieved=eff >= std_eff))

        # 预算执行（2026 逐月）
        budget = None
        with session_scope("business") as bs:
            budget = bs.scalars(select(mz.CarbonBudget).where(mz.CarbonBudget.year == ANCHOR_YEAR)).first()
        monthly_e_budget = budget.energy_budget / 12 if budget else 700
        monthly_c_budget = budget.emission_budget / 12 if budget else 2100
        cum_e = cum_c = 0.0
        for period in ytd_keys:
            m_ce = sum(r["ce_quantity"] for r in monthly_rows if r["period"] == period)
            m_co2 = emission_by_month.get(period, 0.0)
            cum_e += m_ce; cum_c += m_co2
            s.add(ms.BudgetExecution(period=period, budget_type="energy", budget_value=monthly_e_budget,
                                     actual_value=round(m_ce, 2), rate=round(m_ce / monthly_e_budget * 100, 1)))
            s.add(ms.BudgetExecution(period=period, budget_type="carbon", budget_value=monthly_c_budget,
                                     actual_value=round(m_co2, 2), rate=round(m_co2 / monthly_c_budget * 100, 1)))

        # 预警记录
        for period in ytd_keys:
            m_co2 = emission_by_month.get(period, 0.0)
            if m_co2 > monthly_c_budget:
                s.add(ms.AlertRecord(created_at=datetime.now(), alert_type="carbon", level="warning",
                                     message=f"{period} 碳排放 {round(m_co2,1)} tCO2 超出月度预算份额"))
        for cat, code, name, limit_v, unit, direction in LIMIT_STANDARDS:
            if cat == "process":
                actual = ce_by_org.get(code, 0.0) / output_by_org.get(code, 1.0)
                if actual > limit_v:
                    s.add(ms.AlertRecord(created_at=datetime.now(), alert_type="benchmark", level="critical",
                                         message=f"{name} 单位产品能耗 {round(actual,2)} {unit} 超出限额 {limit_v}"))

    if verbose:
        print(f"[seed] 月份范围 {keys[0]} ~ {keys[-1]}，月度汇总 {len(monthly_rows)} 行，"
              f"计量点 {len(METER_POINTS)} 个，抽样读数 {len(readings)} 条")
    return {"months": len(keys), "monthly_rows": len(monthly_rows), "meter_points": len(METER_POINTS)}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    generate()
