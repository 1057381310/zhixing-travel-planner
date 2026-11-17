# 知行 Zhixing · LangGraph 旅行规划智能体

基于 **LangGraph + LangChain + FastAPI** 构建的企业级多 Agent 旅行规划系统。通过自然语言对话，分步骤完成需求收集、目的地推荐、交通规划、住宿预订、餐饮安排、行程生成与预算汇总，并通过 MCP 协议接入天气、地图、火车票、航班、酒店等真实工具。

## 功能特性

- **多 Agent 协同**：主管 Agent 按状态机流程调度，分阶段完成完整旅行规划。
- **8 步状态机工作流**：需求收集 → 目的地推荐 → 交通规划 → 住宿规划 → 餐饮规划 → 行程生成 → 预算汇总 → 报告生成，支持任意步骤回退重做。
- **MCP 工具接入**：统一管理 6 个 MCP 服务、共 37 个工具，单个服务故障不影响其他服务。
- **RAG 知识库**：基于 Chroma 向量库 + BM25 的混合检索，结合目的地资料给出可解释推荐。
- **长期记忆**：记录用户旅行风格、饮食禁忌、住宿偏好与历史出行记录。
- **流式对话**：SSE 实时输出 Token 与工具调用过程。
- **自带 Web 界面**：开箱即用的前端页面，无需额外搭建。

## 技术栈

| 分类 | 技术 |
|---|---|
| Agent 框架 | LangGraph 1.x、LangChain 1.x、langchain-mcp-adapters |
| Web 框架 | FastAPI、Uvicorn |
| 大模型 | 通义千问 Qwen（DashScope，OpenAI 兼容接口） |
| 数据库 | PostgreSQL（Checkpointer / Store / 业务数据）、Redis（缓存） |
| 向量库 | ChromaDB |
| 检索 | sentence-transformers、rank-bm25、jieba |
| MCP 服务端 | FastMCP（自建天气、搜索服务） |

## 目录结构

```
FastAPIProject9/
├── app/
│   ├── agents/            # Agent 定义、状态机中间件、子 Agent
│   ├── api/v1/            # 用户、会话、对话路由
│   ├── core/              # 配置、状态、中间件、Store、检查点
│   ├── mcp_core/          # MCP 客户端管理与自建 MCP 服务
│   ├── models/            # SQLAlchemy 数据模型
│   ├── rag/               # 文档加载、向量库、检索、重排
│   ├── schemas/           # Pydantic 模型
│   ├── tools/             # 状态转换、MCP/RAG/记忆工具
│   └── utils/             # 日志、安全工具
├── data/
│   ├── documents/         # 目的地资料（随仓库提供）
│   └── vectorstore/       # 向量库（运行时生成，已忽略）
├── static/                # 前端页面
├── tests/                 # 测试用例
├── scripts/               # 辅助脚本
├── logs/                  # 运行日志（已忽略）
├── run_local.py           # 本地启动入口（Windows 兼容）
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## 快速开始

### 1. 环境要求

- Python 3.11+
- PostgreSQL 与 Redis（可用项目自带的 `docker-compose.yml` 启动）

### 2. 安装依赖

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 配置环境变量

复制示例配置并填入你自己的密钥：

```bash
cp .env.example .env
```

### 4. 启动服务

```bash
python run_local.py
```

启动后访问：

- 应用界面：http://127.0.0.1:14726
- 接口文档：http://127.0.0.1:14726/docs
- 健康检查：http://127.0.0.1:14726/health

## 环境变量说明

| 变量 | 说明 |
|---|---|
| `DASHSCOPE_API_KEY` | 通义千问 API Key |
| `QWEN_MODEL_NAME` | 模型名称，默认 `qwen-max` |
| `QWEN_BASE_URL` | OpenAI 兼容接口地址 |
| `POSTGRES_*` / `DATABASE_URL` | PostgreSQL 连接配置 |
| `REDIS_*` | Redis 连接配置 |
| `AMAP_API_KEY` | 高德地图 Key |
| `TAVILY_API_KEY` | Tavily 联网搜索 Key |
| `VARIFLIGHT_API_KEY` | VariFlight 航班 Key |
| `AIGOHOTEL_MCP_API` | RollingGo 酒店 MCP Key（`mcp_` 开头） |

> 所有 `.env` 文件均已通过 `.gitignore` 忽略，不会提交到仓库。

## MCP 服务一览

| 服务 | 工具数 | 用途 |
|---|---|---|
| weather | 1 | 天气查询（自建 FastMCP） |
| search | 1 | 联网搜索（自建 FastMCP） |
| amap | 15 | 高德地图、地理编码、路线、周边 POI |
| 12306-mcp | 7 | 火车票查询、余票、换乘 |
| VariFlight | 9 | 航班查询、动态、价格 |
| aigohotel | 4 | 酒店搜索、详情、房型与取消政策 |

## 安全说明

仓库通过 `.gitignore` 严格排除环境变量、密钥、虚拟环境、日志、向量库与运行产物；请勿将包含真实凭据的文件提交到版本库。
