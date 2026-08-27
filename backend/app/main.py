# -*- coding: utf-8 -*-
"""企业能源与碳排放管理平台 — FastAPI 入口。

- CORS 全开
- 注册 /api/v1 业务路由
- lifespan 启停采集模拟器与后台落库任务
- 前端构建产物存在时托管静态资源，并对非 /api、非静态文件的 GET 路径做 SPA 回退
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from app import config
from app.core.response import ok, fail
from app.ingest.simulator import MeterSimulator
from app.ingest.writer import QueueWriter
from app.api.v1 import energy, carbon, collection, overview


def _startup_db_bootstrap():
    """启动兑底：幂等建表（仅建表不灌数）+ 按保留策略清理过期采集数据。"""
    from sqlalchemy import delete
    from app.core.database import create_all_tables, session_scope
    from app.models.collection import MeterReading

    create_all_tables()
    cutoff = datetime.now() - timedelta(days=config.RETENTION_DAYS)
    with session_scope("collection") as session:
        session.execute(delete(MeterReading).where(MeterReading.ts < cutoff))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动：兑底建表 → 建队列 → 起后台落库任务 → 起模拟仪表源；关闭时反序停止。"""
    await asyncio.to_thread(_startup_db_bootstrap)
    queue = asyncio.Queue(maxsize=config.INGEST_QUEUE_MAX)
    writer = QueueWriter(queue)
    simulator = MeterSimulator(queue)
    app.state.queue = queue
    app.state.writer = writer
    app.state.simulator = simulator
    app.state.started_at = datetime.now()
    writer.start()
    await simulator.start()
    yield
    await simulator.stop()
    await writer.stop()


app = FastAPI(
    title="长沙水泵厂能碳管理中心",
    description="12 项业务功能 · 四库架构 · GB/T 2589 / GB/T 32151 / GB/T 24067",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(energy.router, prefix="/api/v1")
app.include_router(carbon.router, prefix="/api/v1")
app.include_router(collection.router, prefix="/api/v1")
app.include_router(overview.router, prefix="/api/v1")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """全局兑底：未捕获异常也保持统一响应契约。"""
    import traceback
    traceback.print_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"code": 50000, "message": "服务内部错误", "data": None},
    )


@app.get("/api/v1/health", include_in_schema=False)
def health():
    return ok({
        "status": "running",
        "queue_size": app.state.queue.qsize() if hasattr(app.state, "queue") else 0,
        "written": app.state.writer.total_written if hasattr(app.state, "writer") else 0,
        "simulator_points": len(app.state.simulator.points) if hasattr(app.state, "simulator") else 0,
    })


# ---------- 静态托管 + SPA 回退（仅当前端构建产物存在） ----------
if config.INDEX_HTML.exists():
    _STATIC_ROOT = config.STATIC_DIR.resolve()

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        """非 /api 的 GET：命中静态文件则返回文件，否则回退 index.html（SPA 路由）。"""
        if full_path.startswith("api/") or full_path == "api":
            return JSONResponse(status_code=404, content=fail(404, "接口不存在"))
        if full_path:
            candidate = (config.STATIC_DIR / full_path).resolve()
            try:
                if candidate.is_file() and candidate.is_relative_to(_STATIC_ROOT):
                    return FileResponse(candidate)
            except OSError:
                pass
        return HTMLResponse(config.INDEX_HTML.read_text(encoding="utf-8"))
