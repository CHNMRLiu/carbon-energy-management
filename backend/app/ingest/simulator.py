# -*- coding: utf-8 -*-
"""simulator.py — 模拟仪表数据源：实现 DataSource，按日负荷曲线生成读数入队。"""
import asyncio
import math
import random
from datetime import datetime

from sqlalchemy import select

from app import config
from app.core.database import session_scope
from app.ingest.base import DataSource
from app.models.collection import MeterPoint


class MeterSimulator(DataSource):
    """每 interval 秒为每个「仪表采集」类计量点生成带日负荷曲线波动的读数。"""

    def __init__(self, queue: asyncio.Queue, interval: float = config.SIMULATOR_INTERVAL):
        self.queue = queue
        self.interval = interval
        self._task = None
        self._running = False
        self.points = []  # [(point_id, rated_value)]

    async def start(self):
        with session_scope("collection") as session:
            rows = session.scalars(
                select(MeterPoint).where(
                    MeterPoint.collect_method == "仪表采集",
                    MeterPoint.status == "normal",
                )
            ).all()
            self.points = [(p.id, p.rated_value or 100.0) for p in rows]
        self._running = True
        if self.points:
            self._task = asyncio.get_running_loop().create_task(self._loop())

    @staticmethod
    def daily_factor(now: datetime) -> float:
        """日负荷曲线：上午/下午双高峰，夜间低谷。"""
        hour = now.hour + now.minute / 60.0
        curve = (
            0.55
            + 0.45 * math.exp(-((hour - 10.0) ** 2) / 8.0)
            + 0.40 * math.exp(-((hour - 15.5) ** 2) / 10.0)
        )
        return min(curve, 1.15)

    async def _loop(self):
        while self._running:
            now = datetime.now()
            factor = self.daily_factor(now)
            for point_id, rated in self.points:
                value = round(rated * factor * random.uniform(0.92, 1.08), 2)
                try:
                    self.queue.put_nowait({
                        "point_id": point_id,
                        "ts": now,
                        "value": value,
                        "quality": "good",
                        "source": "simulator",
                    })
                except asyncio.QueueFull:
                    break
            await asyncio.sleep(self.interval)

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
