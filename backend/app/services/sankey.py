# -*- coding: utf-8 -*-
"""sankey.py — 能流桑基图：能源输入→转换→分配→利用→损失 的 nodes/links（单位 tce）。"""

# 分配权重（转换中心 → 各车间）
WORKSHOP_WEIGHTS = [("一车间", 0.40), ("二车间", 0.35), ("三车间", 0.25)]
# 车间端损失率（输配+转换损失）
LOSS_RATE = 0.08


def build(energy_ce_map: dict, names: dict):
    """energy_ce_map: {energy_code: tce}。返回 (nodes, links, total_input)。"""
    nodes, links = [], []
    seen = set()

    def add_node(name):
        if name not in seen:
            seen.add(name)
            nodes.append({"name": name})

    conv = "能源转换中心"
    util = "生产利用"
    loss = "转换输配损失"

    total = 0.0
    for code, value in energy_ce_map.items():
        if value <= 0:
            continue
        src = f"{names.get(code, code)}输入"
        add_node(src)
        links.append({"source": src, "target": conv, "value": round(value, 3)})
        total += value
    if total <= 0:
        return nodes, links, 0.0
    add_node(conv)

    for workshop, weight in WORKSHOP_WEIGHTS:
        add_node(workshop)
        flow = total * weight
        links.append({"source": conv, "target": workshop, "value": round(flow, 3)})
        links.append({"source": workshop, "target": util, "value": round(flow * (1 - LOSS_RATE), 3)})
        links.append({"source": workshop, "target": loss, "value": round(flow * LOSS_RATE, 3)})
    add_node(util)
    add_node(loss)
    return nodes, links, round(total, 2)
