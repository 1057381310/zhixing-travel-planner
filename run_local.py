#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
本地启动脚本（Windows 兼容）

- 强制 SelectorEventLoop：psycopg 不支持默认的 ProactorEventLoop
- 端口 14726：避开本机 8000 端口上的其他服务

用法：
    .venv\\Scripts\\python run_local.py
"""
import sys
import asyncio
import selectors

# 必须在导入任何其他模块之前设置
if sys.platform == "win32":
    selector = selectors.SelectSelector()
    loop = asyncio.SelectorEventLoop(selector)
    asyncio.set_event_loop(loop)
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    config = uvicorn.Config(
        "app.main:app",
        host="0.0.0.0",
        port=14726,
        reload=False,
        loop="none",  # 不允许 uvicorn 自行创建事件循环
    )
    server = uvicorn.Server(config)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(server.serve())
