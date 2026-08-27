# -*- coding: utf-8 -*-
"""report_export.py — 碳核查报告文本与 CSV 导出（UTF-8 BOM，纯 Python）。"""
import csv
import io
from datetime import datetime

CSV_HEADERS = ["能源类型", "期间范围", "活动水平数据量", "单位", "排放因子", "排放量(tCO2)", "数据来源", "采集方式"]


def build_audit_report(context: dict) -> str:
    """生成碳核查支撑报告文本。"""
    lines = [
        "企业温室气体排放核算报告（碳核查支撑材料）",
        "=" * 40,
        f"报告期间：{context.get('period_label', '')}",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"排放总量：{context.get('total_emission', 0):,.2f} tCO2",
        "",
        "一、核算方法与标准依据",
    ]
    for std in context.get("standards", []):
        lines.append(f"  - {std['code']}《{std['name']}》：{std['scope']}")
    lines += ["", "二、分能源活动水平与排放明细"]
    for item in context.get("items", []):
        lines.append(
            f"  {item['energy_name']}：活动水平 {item['quantity']:,.2f} {item['unit']}，"
            f"排放因子 {item['factor']} tCO2/{item['unit']}，排放量 {item['emission']:,.2f} tCO2，"
            f"数据来自{item['collect_method']}"
        )
    basis = context.get("data_basis", {})
    lines += [
        "",
        "三、数据质量与溯源",
        f"  仪表采集原始记录 {basis.get('meter_readings', 0)} 条",
        f"  手工填报单 {basis.get('manual_reports', 0)} 条",
        f"  计量点覆盖采集方式：{'、'.join(basis.get('methods', []))}",
        "",
        "四、结论",
        f"  本报告期间企业温室气体排放总量为 {context.get('total_emission', 0):,.2f} tCO2，"
        "核算过程可溯源至采集库原始记录，满足碳核查数据要求。",
    ]
    return "\n".join(lines)


def build_audit_csv(rows: list) -> bytes:
    """rows: 与 CSV_HEADERS 对应的 dict 列表；返回带 UTF-8 BOM 的字节串。"""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_HEADERS)
    for r in rows:
        writer.writerow([
            r.get("energy_name", ""), r.get("period_label", ""), f"{r.get('quantity', 0):,.2f}",
            r.get("unit", ""), r.get("factor", ""), f"{r.get('emission', 0):,.2f}",
            r.get("source", "GB/T 32151"), r.get("collect_method", ""),
        ])
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")
