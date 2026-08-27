# -*- coding: utf-8 -*-
r"""一键建表 + 灌模拟数据。

用法（在仓库根目录，使用 venv 解释器）：
    backend\.venv\Scripts\python.exe scripts\init_db.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    from app import config
    from app.core.database import create_all_tables

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("[init_db] 创建四库表结构（幂等）...")
    create_all_tables()

    from app.seed.generate import generate
    print("[init_db] 生成模拟数据（固定随机种子）...")
    stats = generate(verbose=False)
    print(f"[init_db] 完成：{stats}")

    from sqlalchemy import text
    from app.core.database import get_engine
    for name in ("base", "collection", "business", "statistics"):
        with get_engine(name).connect() as conn:
            tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
            mode = conn.execute(text("PRAGMA journal_mode")).scalar()
            print(f"[init_db] {name}.db  journal_mode={mode}  tables={[t[0] for t in tables]}")
    print("[init_db] 全部就绪，可运行 backend/run.py 启动服务（端口 8001）。")


if __name__ == "__main__":
    main()
