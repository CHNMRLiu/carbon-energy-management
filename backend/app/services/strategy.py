# -*- coding: utf-8 -*-
"""strategy.py — 用能结构/成本/能效分析与策略推荐（规则引擎，纯 Python）。"""


def recommend(structure: list, cost_rows: list, efficiency_trend: list, benchmark_items: list):
    """输入结构占比、成本构成、单位产品能耗趋势、对标结果，输出策略推荐列表。"""
    suggestions = []
    struct_map = {r["energy_code"]: r for r in structure}
    cost_map = {r["energy_code"]: r for r in cost_rows}

    elec_struct = struct_map.get("electricity", {})
    elec_cost = cost_map.get("electricity", {})
    coal_struct = struct_map.get("coal", {})

    if elec_cost.get("share", 0) >= 45:
        suggestions.append({
            "dimension": "成本优化", "priority": "高",
            "suggestion": "电力成本占比偏高，建议利用峰谷电价将高耗能工序排至谷段，并评估储能与需量管理",
            "expected_effect": "电费支出预计下降 5%~8%",
        })
    if elec_struct.get("share", 0) >= 35:
        suggestions.append({
            "dimension": "用能结构", "priority": "高",
            "suggestion": "电力折标占比超过 35%，建议扩大屋顶光伏与绿电采购，降低外购电依赖",
            "expected_effect": "外购电占比下降，碳排强度同步改善",
        })
    if coal_struct.get("share", 0) >= 25:
        suggestions.append({
            "dimension": "用能结构", "priority": "中",
            "suggestion": "煤炭占比仍较高，建议实施煤改气/电气化替代，优先替代低效用煤设备",
            "expected_effect": "折标煤与颗粒物排放双下降",
        })

    # 能效趋势：近 3 期均值高于前 3 期（单位产品能耗上升=变差）
    if len(efficiency_trend) >= 6:
        vals = [p["value"] for p in efficiency_trend if p["value"] is not None]
        if len(vals) >= 6:
            recent = sum(vals[-3:]) / 3
            previous = sum(vals[-6:-3]) / 3
            if previous and recent > previous * 1.02:
                suggestions.append({
                    "dimension": "能效管理", "priority": "高",
                    "suggestion": f"单位产品能耗呈上升趋势（近3期均值 {round(recent,2)} kgce/t），建议开展专项能效诊断与设备检修",
                    "expected_effect": "扭转能效劣化趋势",
                })
            elif previous and recent < previous * 0.98:
                suggestions.append({
                    "dimension": "能效管理", "priority": "低",
                    "suggestion": "单位产品能耗持续改善，建议固化当前运行参数并纳入标准化作业",
                    "expected_effect": "维持改善成果",
                })

    failed = [i for i in benchmark_items if not i["achieved"]]
    for item in failed[:3]:
        suggestions.append({
            "dimension": "能效对标", "priority": "高",
            "suggestion": f"{item['item_name']} 未达标（实际 {item['actual_value']} / 限额 {item['limit_value']} {item['unit']}），{item['advice']}",
            "expected_effect": "达到国家限额标准",
        })
    if not suggestions:
        suggestions.append({
            "dimension": "综合", "priority": "低",
            "suggestion": "各项指标正常，建议持续跟踪并完善班组能耗考核",
            "expected_effect": "精细化管理",
        })
    order = {"高": 0, "中": 1, "低": 2}
    suggestions.sort(key=lambda s: order.get(s["priority"], 3))
    return suggestions
