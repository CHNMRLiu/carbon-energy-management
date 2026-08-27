# -*- coding: utf-8 -*-
"""启动入口：在 backend/ 目录下执行 `python run.py`，监听 127.0.0.1:8001。"""
import sys

import uvicorn

from app.config import HOST, PORT

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    uvicorn.run("app.main:app", host=HOST, port=PORT, log_level="info")
