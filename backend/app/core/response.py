# -*- coding: utf-8 -*-
"""统一响应封装：{"code":0,"message":"ok","data":...}"""
from typing import Any, Optional


def ok(data: Any = None, message: str = "ok") -> dict:
    return {"code": 0, "message": message, "data": data}


def fail(code: int = 1, message: str = "error", data: Any = None) -> dict:
    return {"code": code, "message": message, "data": data}


def round_or_none(value, ndigits: int = 4) -> Optional[float]:
    return None if value is None else round(float(value), ndigits)
