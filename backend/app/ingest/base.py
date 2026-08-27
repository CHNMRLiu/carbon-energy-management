# -*- coding: utf-8 -*-
"""DataSource 抽象：所有采集源（模拟器/真实驱动）统一生命周期。"""
from abc import ABC, abstractmethod


class DataSource(ABC):
    """数据源抽象基类：在 FastAPI lifespan 中 start/stop。"""

    @abstractmethod
    async def start(self):
        """启动数据源（通常为后台任务）。"""

    @abstractmethod
    async def stop(self):
        """停止数据源并释放资源。"""
