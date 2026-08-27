# -*- coding: utf-8 -*-
r"""后端端到端冒烟测试（需先启动后端：127.0.0.1:8001）。

backend\.venv\Scripts\python.exe scripts\smoke_test.py
"""
import json
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8001"
API = BASE + "/api/v1"
DB = Path(__file__).resolve().parent.parent / "backend" / "data" / "collection.db"

GET_ENDPOINTS = [
    "/energy/consumption?energy_type=&period=month&start=&end=",
    "/energy/consumption?period=year",
    "/energy/calculation?period=month",
    "/energy/calculation?period=year",
    "/energy/analysis",
    "/energy/benchmark",
    "/energy/flow",
    "/energy/optimization",
    "/carbon/budget",
    "/carbon/emission",
    "/carbon/footprint",
    "/carbon/supply-chain",
    "/carbon/audit",
    "/carbon/asset",
    "/overview",
    "/ingest/points",
]

passed, failed = [], []


def http(method, url, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status, resp.headers, resp.read()


def check(name, cond, detail=""):
    (failed if not cond else passed).append(name)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {detail}")


print("== 1. GET 端点冒烟 ==")
for path in GET_ENDPOINTS:
    try:
        status, _, body = http("GET", API + path)
        data = json.loads(body.decode("utf-8"))
        check(f"GET {path}", status == 200 and data.get("code") == 0, f"status={status}")
    except Exception as exc:
        check(f"GET {path}", False, str(exc))

print("== 2. 桑基图结构 ==")
_, _, body = http("GET", API + "/energy/flow")
flow = json.loads(body.decode("utf-8"))["data"]
check("sankey nodes 非空", len(flow["nodes"]) > 0, f"n={len(flow['nodes'])}")
check("sankey links 非空", len(flow["links"]) > 0, f"n={len(flow['links'])}")
node_names = {n["name"] for n in flow["nodes"]}
check("links 节点引用合法", all(l["source"] in node_names and l["target"] in node_names for l in flow["links"]))

print("== 3. 仪表上报 202 且落库 ==")
_, _, body = http("GET", API + "/ingest/points")
points = json.loads(body.decode("utf-8"))["data"]["items"]
target = next(p for p in points if p["collect_method"] == "仪表采集")
before = sqlite3.connect(str(DB))
count_before = before.execute("SELECT COUNT(*) FROM meter_reading").fetchone()[0]
before.close()
payload = [{"point_code": target["code"], "value": 1234.5, "quality": "good"} for _ in range(3)]
status, _, body = http("POST", API + "/ingest/meter", payload)
ack = json.loads(body.decode("utf-8"))
check("POST /ingest/meter 返回 202", status == 202, f"status={status}")
check("accepted=3", ack["data"]["accepted"] == 3)
time.sleep(6)  # 等待后台落库
after = sqlite3.connect(str(DB))
count_after = after.execute("SELECT COUNT(*) FROM meter_reading").fetchone()[0]
after.close()
check("上报数据已落库", count_after >= count_before + 3, f"{count_before} -> {count_after}")

print("== 4. 手工填报/系统对接/烟感 ==")
status, _, body = http("POST", API + "/ingest/manual",
                       {"point_code": "EP020", "period": "2026-08", "value": 9500.0, "reporter": "冒烟测试"})
check("POST /ingest/manual", status == 200 and json.loads(body.decode('utf-8'))["code"] == 0)
status, _, body = http("POST", API + "/ingest/external",
                       [{"point_code": "EP001", "value": 26000.0}])
check("POST /ingest/external 202", status == 202)
status, _, body = http("POST", API + "/ingest/smoke",
                       [{"point_code": "EP030", "value": 880.0}])
check("POST /ingest/smoke 202", status == 202)

print("== 5. CSV 导出（BOM + 附件头） ==")
status, headers, body = http("GET", API + "/carbon/audit/export")
check("导出返回 200", status == 200)
check("Content-Disposition 附件", "attachment" in headers.get("Content-Disposition", ""),
      headers.get("Content-Disposition", ""))
check("CSV 带 UTF-8 BOM", body.startswith(b"\xef\xbb\xbf"))

print("== 6. SPA 回退与静态托管 ==")
status, headers, body = http("GET", BASE + "/")
check("GET / 返回 index.html", status == 200 and b"<html" in body.lower())
status, headers, body = http("GET", BASE + "/screen")
check("GET /screen SPA 回退", status == 200 and b"<html" in body.lower())

print(f"\n结果：{len(passed)} 通过 / {len(failed)} 失败")
if failed:
    print("失败项：", failed)
    sys.exit(1)
