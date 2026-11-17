#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/1/8 17:37
@Author  : GGBOND
@File    : search_server.py
@Software: PyCharm
"""
"""
MCP 客户端管理器
统一管理所有 MCP 服务连接
"""
import asyncio
import os
import sys
from typing import Optional, List
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from app.utils.logger import app_logger

load_dotenv()


class MCPClientManager:
    """
    MCP 客户端管理器（单例模式）
    """

    _instance: Optional['MCPClientManager'] = None
    _client: Optional[MultiServerMCPClient] = None
    _tools: Optional[List] = None
    _lock = asyncio.Lock()

    # 项目根目录（用于 stdio 服务）
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

    # 环境变量（追加 PYTHONPATH）
    ENV_VARS = os.environ.copy()
    ENV_VARS["PYTHONPATH"] = PROJECT_ROOT + os.pathsep + ENV_VARS.get("PYTHONPATH", "")

    # 服务器配置
    SERVER_CONFIGS = {
        # ========== 自建服务（stdio） ==========
        "weather": {
            "command": sys.executable,
            "args": ["-m", "app.mcp_core.servers.weather_server"],
            "transport": "stdio",
            "env": ENV_VARS,
        },
        "search": {
            "command": sys.executable,
            "args": ["-m", "app.mcp_core.servers.search_server"],
            "transport": "stdio",
            "env": ENV_VARS,
        },

        # ========== 外部服务（HTTP） ==========
        "amap": {
            "url": f"https://mcp.amap.com/mcp?key={os.getenv('AMAP_API_KEY', '')}",
            "transport": "http",
        },
        "12306-mcp": {
            # 本地自部署的 drfccv/mcp-server-12306（Streamable HTTP，端口 8090）
            "url": "http://127.0.0.1:8090/mcp",
            "transport": "streamable_http",
        },
        "VariFlight-Aviation": {
            "url": f"https://ai.variflight.com/servers/aviation/mcp/?api_key={os.getenv('VARIFLIGHT_API_KEY', '')}",
            "transport": "streamable_http",
        },
        "aigohotel-mcp": {
            # RollingGo（原 AigoHotel）官方当前标准端点，Bearer 认证
            "url": "https://mcp.rollinggo.cn/mcp",
            "transport": "streamable_http",
            "headers": {
                "Authorization": f"Bearer {os.getenv('AIGOHOTEL_MCP_API')}",
                "Content-Type": "application/json"
            }
        },
    }

    @classmethod
    async def get_instance(cls, servers: List[str] = None) -> 'MCPClientManager':
        """获取单例实例"""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance.initialize(servers=servers)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """重置单例（用于测试）"""
        cls._instance = None

    async def initialize(self, servers: List[str] = None):
        """
        初始化 MCP 客户端

        Args:
            servers: 要启用的服务列表，默认启用所有
        """
        if self._client is not None:
            app_logger.warning("⚠️ MCP 客户端已初始化，跳过")
            return

        # 默认启用所有服务
        servers = servers or list(self.SERVER_CONFIGS.keys())
        configs = {k: v for k, v in self.SERVER_CONFIGS.items() if k in servers}

        app_logger.info(f"🔗 初始化 MCP: {list(configs.keys())}")

        # 创建客户端（保留完整配置，供后续按需使用）
        self._client = MultiServerMCPClient(configs)

        # 容错预加载：逐个服务连接，单个服务失败不影响其他服务的工具
        tools: List = []
        available: List[str] = []
        for name in servers:
            try:
                single_client = MultiServerMCPClient({name: self.SERVER_CONFIGS[name]})
                server_tools = await asyncio.wait_for(single_client.get_tools(), timeout=30)
                tools.extend(server_tools)
                available.append(name)
                app_logger.info(f"  ✓ {name}: {len(server_tools)} 个工具")
            except Exception as e:
                app_logger.warning(f"  ✗ {name} 不可用，已跳过: {type(e).__name__}: {e}")

        self._tools = tools
        app_logger.info(
            f"✅ MCP 就绪：{len(available)}/{len(servers)} 个服务、共 {len(self._tools)} 个工具 "
            f"(可用: {available})"
        )

    async def close(self):
        """关闭客户端"""
        if self._client:
            self._client = None
            self._tools = None
            app_logger.info("🔒 MCP 客户端已关闭")

    async def get_tools(self) -> List:
        """
        获取所有 MCP 工具

        Returns:
            LangChain 工具列表
        """
        if self._client is None:
            raise RuntimeError("MCP 客户端未初始化，请先调用 initialize()")

        # 如果已缓存，直接返回
        if self._tools:
            return self._tools

        # 否则重新获取
        self._tools = await self._client.get_tools()
        return self._tools


async def get_mcp_client(servers: List[str] = None) -> MCPClientManager:
    """获取 MCP 客户端管理器实例"""
    return await MCPClientManager.get_instance(servers)