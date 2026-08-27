# 工业企业和园区数字化能碳管理中心

> 一站式能碳数据监测、核算、分析与决策平台

[![Version](https://img.shields.io/badge/version-0.1.1-blue)]()
[![Python](https://img.shields.io/badge/python-3.10+-green)]()
[![Vue](https://img.shields.io/badge/vue-3.4+-brightgreen)]()
[![FastAPI](https://img.shields.io/badge/fastapi-0.115+-teal)]()
[![License](https://img.shields.io/badge/license-MIT-yellow)]()

---

## 项目简介

本系统面向工业企业和园区，提供能源消耗监测、碳排放核算、碳足迹分析、能效对标与优化、碳资产管理等全链路数字化能碳管理能力。系统采用前后端分离架构，后端基于 Python FastAPI + SQLite，前端基于 Vue 3 + Element Plus + ECharts，支持单机轻量部署。

### 核心能力

- **能耗管理**：多能源实时查询、综合能耗计算、能效统计、用能分析与策略推荐、能效对标、能流桑基图分析、能效平衡与优化
- **碳管理**：碳预算、碳排放核算、产品碳足迹（五阶段）、供应链碳管理、碳核查支撑、碳资产管理
- **数据采集**：系统对接、IoT 仪表采集、手工填报、烟感实测四种方式统一接入
- **可视化大屏**：能碳驾驶舱，实时 KPI、趋势图、桑基图、仪表盘，支持日夜主题切换

---

## 技术架构

```
┌─────────────────────────────────────────────┐
│                  前端 (Vue 3)                │
│  Element Plus · ECharts · Pinia · Vue Router │
│  管理端 (13 页面) + 可视化大屏 (1 页面)        │
└──────────────────┬──────────────────────────┘
                   │ HTTP REST API
┌──────────────────▼──────────────────────────┐
│              后端 (FastAPI)                   │
│  SQLAlchemy · SQLite · 四库分离架构            │
│  base · collection · business · statistics    │
└─────────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术 |
|------|------|
| **前端框架** | Vue 3.4+、Vite 6、Pinia、Vue Router 4 |
| **UI 组件** | Element Plus |
| **图表** | Apache ECharts 5 |
| **后端框架** | FastAPI 0.115+、Uvicorn |
| **ORM** | SQLAlchemy 2.0 |
| **数据库** | SQLite（四库分离：base / collection / business / statistics） |
| **Python 版本** | 3.10+ |

---

## 功能模块

### 管理端（13 个功能页面）

| 编号 | 模块 | 页面 | 说明 |
|------|------|------|------|
| 01 | 能耗管理 | 能耗查询 | 多能源实时查询与历史追溯，折标依据 GB/T 2589 |
| 02 | 能耗管理 | 能耗计算 | 综合能耗、单位产品能耗、单位产值能耗，同比环比分析 |
| 03 | 能耗管理 | 用能分析与策略推荐 | 用能结构、成本构成、能效趋势三维分析，输出节能优化策略 |
| 04 | 能耗管理 | 能效对标 | 工序、产品、设备三级对标，限额依据国家能耗限额标准 |
| 05 | 能耗管理 | 能流分析 | 能源输入→转换→分配→利用全过程桑基图展示 |
| 06 | 能耗管理 | 能效平衡与优化 | AI 模型分析工艺与设备参数，输出最优设定与预计节能量 |
| 07 | 碳管理 | 碳预算管理 | 年度用能与碳排放预算执行率、年末预测与预警 |
| 08 | 碳管理 | 碳排放核算 | 总量与强度核算、来源拆分、月度趋势与预警 |
| 09 | 碳管理 | 产品碳足迹 | 全生命周期五阶段碳足迹核算，碳标识等级评定 |
| 10 | 碳管理 | 供应链碳管理 | 上下游企业碳数据采集、核算与足迹共享 |
| 11 | 碳管理 | 碳核查支撑 | 排放数据全链路溯源，核查材料一键导出（CSV/TXT） |
| 12 | 碳管理 | 碳资产管理 | 配额管理、履约测算、预测预警 |
| IN | 数据采集 | 采集与手工填报 | 四种采集方式统一管理，支持手工数据填报 |

### 可视化大屏

- 综合能耗趋势（柱状图）
- 能源结构占比（环形图）
- 全厂能流全景（桑基图）
- 碳排放月度趋势（折线面积图）
- 碳配额仪表盘（仪表图）
- 底部 KPI：综合能耗累计、碳排放累计、实时功率、碳配额盈余
- 支持日夜主题切换

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 16+
- Windows / Linux / macOS

### 安装与启动

```bash
# 1. 克隆仓库
git clone https://github.com/ChangyangOpenSource/carbon-energy-management.git
cd carbon-energy-management

# 2. 后端：创建虚拟环境并安装依赖
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt

# 3. 初始化数据库（建表 + 灌入模拟数据）
cd ..
backend\.venv\Scripts\python.exe scripts\init_db.py

# 4. 前端：安装依赖并构建
cd frontend
npm install
npm run build

# 5. 启动服务
cd ..\backend
python run.py
```

启动后访问：

| 地址 | 说明 |
|------|------|
| http://127.0.0.1:8001/ | 管理端 |
| http://127.0.0.1:8001/screen | 可视化大屏 |
| http://127.0.0.1:8001/docs | Swagger API 文档 |

### 一键启动（Windows）

```powershell
.\start.ps1
```

---

## 项目结构

```
carbon-energy-management/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/v1/             # REST API 路由
│   │   │   ├── overview.py     # 大屏汇总接口
│   │   │   ├── energy.py       # 能耗管理接口
│   │   │   ├── carbon.py       # 碳管理接口
│   │   │   ── collection.py   # 数据采集接口
│   │   ├── core/               # 核心模块（数据库、响应封装）
│   │   ├── models/             # SQLAlchemy 数据模型
│   │   ├── schemas/            # Pydantic 请求/响应模型
│   │   ├── services/           # 业务逻辑层
│   │   ├── seed/               # 模拟数据生成器
│   │   ├── ingest/             # 数据采集引擎
│   │   ├── static/             # 前端构建产物（托管）
│   │   ├── config.py           # 全局配置
│   │   └── main.py             # FastAPI 应用入口
│   ├── data/                   # SQLite 数据库文件
│   ├── requirements.txt
│   └── run.py                  # 启动入口
├── frontend/                   # 前端源码
│   ├── src/
│   │   ├── api/                # API 调用层 + 适配层
│   │   ├── components/         # 通用组件
│   │   ├── composables/        # 组合式函数
│   │   ├── layouts/            # 布局组件
│   │   ├── router/             # 路由配置
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── styles/             # 全局样式（日夜主题）
│   │   ├── views/              # 页面视图
│   │   │   ├── admin/          # 管理端（13 页面）
│   │   │   └── screen/         # 可视化大屏
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
├── scripts/
│   ├── init_db.py              # 数据库初始化脚本
│   └── smoke_test.py           # 冒烟测试脚本
├── .gitignore
└── README.md
```

---

## 数据库设计

系统采用**四库分离**架构，每个 SQLite 数据库负责独立领域：

| 数据库 | 用途 | 主要表 |
|--------|------|--------|
| `base.db` | 基础库 | 能源字典、组织架构、设备台账、排放因子、限额标准、碳配额 |
| `collection.db` | 采集库 | 计量点、小时级读数、手工填报单 |
| `business.db` | 业务库 | 能源账单、产量产值、碳排放、产品碳足迹、供应链、履约记录、碳预算 |
| `statistics.db` | 统计库 | 月度/年度汇总、能效对标结果、预算执行、预警记录 |

---

## 核算标准依据

| 标准编号 | 名称 | 适用范围 |
|----------|------|----------|
| GB/T 2589 | 综合能耗计算通则 | 折标煤 / 综合能耗 |
| GB/T 32151 | 温室气体排放核算与报告要求 | 企业碳排放核算 |
| GB/T 24067 | 产品碳足迹量化要求与指南 | 产品碳足迹 |

---

## 版本历史

### v0.1.1 (2026-08-27)

- 初始版本发布
- 13 个管理端功能页面 + 1 个可视化大屏
- 四库分离 SQLite 架构
- 四种数据采集方式（系统对接 / 仪表采集 / 手工填报 / 烟感实测）
- 日夜主题切换
- 固定种子模拟数据生成器（可重复初始化）

---

## License

MIT License
