# -*- coding: utf-8 -*-
"""writer.py — 后台批量落库：消费进程内 asyncio.Queue，批量写入 collection.db。"""
import asyncio

from app import config
from app.core.database import session_scope
from app.models.collection import MeterReading


class QueueWriter:
    """队列消费器：每 flush_interval 秒（或批量攒满）将读数批量插入数据库。"""

    def __init__(self, queue: asyncio.Queue, flush_interval: float = config.WRITER_FLUSH_INTERVAL):
        self.queue = queue
        self.flush_interval = flush_interval
        self._task = None
        self._running = False
        self.total_written = 0

    def start(self):
        self._running = True
        self._task = asyncio.get_running_loop().create_task(self._run())

    async def _run(self):
        while self._running or not self.queue.empty():
            batch = []
            try:
                item = await asyncio.wait_for(self.queue.get(), timeout=self.flush_interval)
                batch.append(item)
            except (asyncio.TimeoutError, TimeoutError):
                pass
            while not self.queue.empty() and len(batch) < 2000:
                batch.append(self.queue.get_nowait())
            if batch:
                await asyncio.to_thread(self._flush, batch)

    def _flush(self, batch):
        rows = [
            MeterReading(
                point_id=i["point_id"],
                ts=i["ts"],
                value=i["value"],
                quality=i.get("quality", "good"),
                source=i.get("source", "meter"),
            )
            for i in batch
        ]
        with session_scope("collection") as session:
            session.add_all(rows)
        self.total_written += len(rows)

    async def stop(self):
        """停止并排空剩余队列。"""
        self._running = False
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=10)
            except (asyncio.TimeoutError, asyncio.CancelledError, TimeoutError):
                self._task.cancel()
