# -*- coding: utf-8 -*-
"""平台全局配置：路径、端口、GB/T 2589 折标系数等常量。"""
from pathlib import Path

# ---------- 路径 ----------
BASE_DIR = Path(__file__).resolve().parent.parent          # backend/
PROJECT_ROOT = BASE_DIR.parent                             # f:\XLS
DATA_DIR = BASE_DIR / "data"                               # 4 个 SQLite 文件
STATIC_DIR = BASE_DIR / "app" / "static"                   # 前端构建产物
INDEX_HTML = STATIC_DIR / "index.html"

# ---------- 服务 ----------
HOST = "127.0.0.1"
PORT = 8001

# ---------- 四库文件 ----------
DB_FILES = {
    "base": DATA_DIR / "base.db",              # 基础库：字典/台账/标准/因子
    "collection": DATA_DIR / "collection.db",  # 采集库：计量点/原始记录/填报
    "business": DATA_DIR / "business.db",      # 业务库：账单/产量/核算/足迹
    "statistics": DATA_DIR / "statistics.db",  # 统计库：汇总/对标/预算/预警
}

# ---------- GB/T 2589 折标系数（kgce / 物理量单位），仅作兜底常量，权威值在 base.db ----------
CE_COEFFICIENTS = {
    "coal": 0.7143,          # kgce/kg
    "electricity": 0.1229,   # kgce/kWh
    "natural_gas": 1.33,     # kgce/m3
    "heat": 0.0341,          # kgce/MJ
    "diesel": 1.4571,        # kgce/kg
}

ENERGY_NAMES = {
    "coal": "煤炭",
    "electricity": "电力",
    "natural_gas": "天然气",
    "heat": "热力",
    "diesel": "柴油",
}

# ---------- 数据采集方式（四种） ----------
COLLECT_METHODS = ("系统对接", "仪表采集", "手工填报", "烟感实测")

# ---------- 采集/模拟参数 ----------
INGEST_QUEUE_MAX = 20000          # 进程内队列上限
INGEST_BATCH_LIMIT = 1000         # 单次上报条数上限
WRITER_FLUSH_INTERVAL = 3.0       # 后台落库周期（秒）
SIMULATOR_INTERVAL = 10.0         # 模拟仪表上报周期（秒）
RETENTION_DAYS = 30               # 采集库 meter_reading 保留天数（启动时清理）

# ---------- 核算标准来源 ----------
STANDARDS = [
    {"code": "GB/T 2589", "name": "综合能耗计算通则", "scope": "折标煤/综合能耗"},
    {"code": "GB/T 32151", "name": "温室气体排放核算与报告要求", "scope": "企业碳排放核算"},
    {"code": "GB/T 24067", "name": "产品碳足迹量化要求与指南", "scope": "产品碳足迹"},
    {"code": "省级温室气体清单编制指南", "name": "省级温室气体清单编制指南", "scope": "园区碳排放"},
]
