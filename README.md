# NBA 历史数据库

一个完整的本地 NBA 历史数据库系统，包含 1946 年至今的完整 NBA 历史数据。支持个人数据分析、Web 应用后端和 AI Agent 集成。

## 🎯 项目目标

- 构建完整的 NBA 历史数据库（1946 年至今）
- 提供 RESTful API 查询接口
- 支持复杂数据分析和时间序列查询
- 提供美观的前端数据可视化界面
- 集成 MCP Server 协议，支持 AI Agent 调用

## 🏗️ 技术栈

### 后端
- **数据库**: PostgreSQL（主库）+ DuckDB（分析加速）
- **Web 框架**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **数据迁移**: Alembic

### 前端
- **框架**: React + TypeScript
- **构建工具**: Vite
- **可视化**: Recharts + D3.js

### 数据获取
- **主力数据源**: [nba_api](https://github.com/swar/nba_api)（Python 封装 stats.nba.com）
- **辅助数据**: Kaggle NBA 数据集

### Agent 集成
- **协议**: MCP Server

## 📊 数据范围

- **时间跨度**: 1946-47 赛季至今（~80 年完整历史）
- **数据量**: 约 1-2GB
- **数据内容**:
  - ✅ 球员信息（~4800+ 名球员）
  - ✅ 基础统计（得分、篮板、助攻等）
  - ✅ 高阶统计（PER、TS%、USG%、ORtg、DRtg 等）
  - ✅ 球队历史（~30 支球队）
  - ✅ 比赛数据（~65000+ 场常规赛 + ~10000+ 场季后赛）
  - ✅ 季后赛对决记录
  - ✅ Play-by-Play 数据
  - ✅ 投篮热图数据

## 📁 项目结构

```
nba-data/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/               # API 路由
│   │   ├── core/              # 核心配置
│   │   ├── models/            # SQLAlchemy 模型
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # 业务逻辑
│   │   └── main.py            # 应用入口
│   ├── migrations/            # Alembic 数据库迁移
│   └── tests/                 # 测试
│
├── data/                      # 数据获取和处理
│   ├── nba_api_client/        # nba_api 封装
│   ├── importers/             # 数据导入脚本
│   ├── processors/            # 数据处理
│   └── scripts/               # 全量/增量更新脚本
│
├── analytics/                 # DuckDB 分析
│   ├── queries/               # SQL 查询模板
│   ├── notebooks/             # Jupyter notebooks
│   └── reports/               # 分析报告
│
├── frontend/                  # React 前端
│   ├── src/
│   │   ├── components/        # React 组件
│   │   ├── pages/             # 页面
│   │   ├── hooks/             # 自定义 hooks
│   │   ├── services/          # API 调用
│   │   └── stores/            # 状态管理
│   └── public/
│
├── mcp-server/                # MCP Server
│   ├── server.py              # MCP Server 实现
│   └── tools/                 # MCP 工具
│
├── docs/                      # 文档
│   ├── research/              # 研究文档
│   ├── api/                   # API 文档
│   └── guides/                # 使用指南
│
└── scripts/                   # 项目脚本
```

## 🚀 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+

### 1. 克隆项目

```bash
git clone <repository-url>
cd nba-data
```

### 2. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，配置数据库连接等信息
```

### 3. 安装后端依赖

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 4. 设置数据库

```bash
# 创建 PostgreSQL 数据库
createdb nba_data

# 运行数据库迁移
alembic upgrade head
```

### 5. 启动后端服务

```bash
cd backend
uvicorn app.main:app --reload
```

访问 http://localhost:8000/docs 查看 API 文档。

### 6. 安装前端依赖（待开发）

```bash
cd frontend
npm install
npm run dev
```

### 7. 导入数据

```bash
# 全量导入（首次，约 2-4 小时）
python data/scripts/full_import.py

# 增量更新（定期运行）
python data/scripts/incremental_update.py
```

## 📖 使用指南

### API 使用

#### 获取球员列表
```bash
curl http://localhost:8000/api/v1/players
```

#### 获取球员详情
```bash
curl http://localhost:8000/api/v1/players/2544
```

#### 获取球员统计
```bash
curl http://localhost:8000/api/v1/players/2544/stats?season=2023-24
```

### 数据分析

使用 DuckDB 进行复杂分析：

```python
import duckdb

conn = duckdb.connect('analytics/nba_analytics.db')
result = conn.execute("""
    SELECT full_name, points_per_game, player_efficiency_rating
    FROM player_season_stats
    WHERE season_id = '2023-24'
    ORDER BY points_per_game DESC
    LIMIT 10
""").fetchdf()
print(result)
```

### MCP Server 使用

AI Agent 可以通过 MCP 协议调用：

```python
from mcp import Client

client = Client("nba-data-server")
result = client.call_tool("query_player", {"name": "LeBron James"})
print(result)
```

## 🔧 开发计划

- [x] Phase 1: 基础设施搭建
- [x] Phase 2: 数据获取和导入
- [ ] Phase 3: 后端 API 开发
- [ ] Phase 4: 前端开发
- [ ] Phase 5: MCP Server
- [ ] Phase 6: 优化和文档

## 📚 参考资源

- [nba_api 文档](https://github.com/swar/nba_api)
- [FastAPI 文档](https://fastapi.tiangolo.com)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org)
- [React 文档](https://react.dev)
- [MCP 协议](https://modelcontextprotocol.io)
- [NBA 数据源研究](docs/research/nba-data-sources.md)

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## ⚠️ 免责声明

本项目仅供学习和研究使用。NBA 数据版权归 NBA 官方所有，请勿用于商业用途。
