# -*- coding: utf-8 -*-
"""四库 engine / SessionLocal 工厂 + FastAPI 依赖。

四个 SQLite 文件各建独立 engine，连接时开启 WAL 模式。
"""
from contextlib import contextmanager

import sqlalchemy
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.config import DB_FILES

_engines: dict = {}
_session_factories: dict = {}


def _make_engine(db_path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
        future=True,
    )

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_conn, _record):  # pragma: no cover
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA wal_autocheckpoint=1000")  # 自动checkpoint
        cursor.close()

    return engine


def get_engine(name: str):
    """按库名获取（懒创建）engine：base / collection / business / statistics。"""
    if name not in _engines:
        if name not in DB_FILES:
            raise KeyError(f"未知数据库: {name}")
        _engines[name] = _make_engine(DB_FILES[name])
    return _engines[name]


def get_session_factory(name: str):
    if name not in _session_factories:
        _session_factories[name] = sessionmaker(
            bind=get_engine(name), autoflush=False, expire_on_commit=False, future=True
        )
    return _session_factories[name]


@contextmanager
def session_scope(name: str):
    """业务代码统一入口：with session_scope("base") as s: ..."""
    session = get_session_factory(name)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------- FastAPI 依赖 ----------
def get_base_db():
    with session_scope("base") as session:
        yield session


def get_collection_db():
    with session_scope("collection") as session:
        yield session


def get_business_db():
    with session_scope("business") as session:
        yield session


def get_statistics_db():
    with session_scope("statistics") as session:
        yield session


def create_all_tables():
    """对四库执行 metadata.create_all（幂等）。仅在初始化时调用一次。"""
    from app.models.base import Base as BaseBase
    from app.models.collection import Base as CollectionBase
    from app.models.business import Base as BusinessBase
    from app.models.statistics import Base as StatisticsBase

    # 注意：不清除缓存的引擎和会话工厂，避免 WAL 模式下的时序问题
    # _engines.clear()
    # _session_factories.clear()

    BaseBase.metadata.create_all(get_engine("base"))
    CollectionBase.metadata.create_all(get_engine("collection"))
    BusinessBase.metadata.create_all(get_engine("business"))
    StatisticsBase.metadata.create_all(get_engine("statistics"))
    
    # Checkpoint WAL files to ensure data is written to main database
    for name in ["base", "collection", "business", "statistics"]:
        engine = get_engine(name)
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("PRAGMA wal_checkpoint(TRUNCATE)"))
            conn.commit()
