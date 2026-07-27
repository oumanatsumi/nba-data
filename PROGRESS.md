# NBA 历史数据库项目进度总结

> 最后更新：2026-07-27

---

## 项目概览

**目标**：构建本地 NBA 历史数据库，包含 1946 年至今完整数据，支持查询分析、Web API、AI Agent 集成

**技术栈**：
- 数据库：PostgreSQL 17（主库）+ DuckDB（分析）
- 后端：FastAPI + SQLAlchemy 2.0
- 前端：React + TypeScript（待开发）
- 数据源：Kaggle 数据集（nba_api 因网络问题改用离线数据）

---

## 当前状态

### ✅ 已完成

#### 1. 数据库设计与导入
- **8 张核心表**全部填充完成
- 数据量：约 1.2GB PostgreSQL 数据库
- 覆盖：1946-47 至 2025-26 赛季（80 年）

| 表 | 记录数 | 说明 |
|---|--------|------|
| `players` | 6,694 | 球员信息（身高/体重/选秀/国籍） |
| `teams` | 91 | 30 现役 + 61 历史球队 |
| `seasons` | 156 | 完整赛季列表 |
| `games` | 75,218 | 70,542 常规赛 + 4,606 季后赛 + 70 全明星 |
| `player_game_stats` | 1,560,532 | 每场 Box Score |
| `player_season_stats` | 27,904 | 场均 + PER/TS%/USG%/WS/BPM/VORP |
| `team_season_stats` | 2,080 | 球队胜负统计 |
| `playoff_series` | 1,369 | 季后赛对阵 + 比分 |

#### 2. 数据来源
从 3 个 Kaggle 数据集导入：
1. **wyattowalsh/basketball**（2.3GB）- 球员/球队基础、比赛记录
2. **eoinamoore/historical-nba-data**（1.3GB）- 球员单场统计、命中率
3. **sumitrodatta/nba-aba-baa-stats**（20MB）- BBR 进阶统计（PER/WS/BPM/VORP）

#### 3. FastAPI 后端（部分完成）
已编写 API 路由文件：
- `backend/app/api/v1/players.py` - 球员查询、赛季统计、进阶数据
- `backend/app/api/v1/teams.py` - 球队列表、阵容、战绩
- `backend/app/api/v1/games.py` - 比赛列表、Box Score、季后赛
- `backend/app/api/v1/playoffs.py` - 季后赛对阵、历史对决

**已知问题**：`get_db()` 同步/异步冲突需要修复

#### 4. 数据查询验证
已验证两个查询：
- ✅ Q1: 2018 年西部决赛 GSW vs HOU 每场比分（7 场完整）
- ✅ Q2: 2026 年东部决赛 NYK vs CLE 每场最高得分（4 场完整）

---

### 🚧 进行中

#### FastAPI 后端
- [ ] 修复 `get_db()` 同步/异步问题
- [ ] 测试所有 API 端点
- [ ] 添加错误处理和参数验证
- [ ] 编写 API 文档

#### 前端（未开始）
- [ ] React 项目初始化
- [ ] 球员/球队查询页面
- [ ] 数据可视化图表
- [ ] 对比分析功能

#### MCP Server（未开始）
- [ ] MCP Server 实现
- [ ] AI Agent 工具定义

---

## 关键决策

### 数据源选择
**决定**：使用 Kaggle 离线数据集，而非 nba_api

**原因**：
- nba_api 连接 stats.nba.com 被 Akamai 反爬拦截（TLS 指纹识别）
- 即使挂代理也无法绕过
- Kaggle 数据集更稳定，数据完整

### 数据库选型
**决定**：PostgreSQL 17 作为主库

**原因**：
- 数据量 1-2GB，PostgreSQL 完全胜任
- 支持复杂查询、时间序列分析
- 与 DuckDB 配合可加速分析查询
- 社区成熟，文档完善

### 数据导入策略
**决定**：分阶段从多个 Kaggle 数据集导入

**原因**：
- 单一数据集无法覆盖所有需求
- 不同数据集有各自优势（基础 vs 进阶统计）
- 需要合并和去重

---

## 技术细节

### 数据库 Schema
高度规范化设计，8 张核心表：

```
players (player_id PK)
  ├── player_season_stats (FK: player_id, season_id, team_id)
  └── player_game_stats (FK: player_id, game_id, team_id)

teams (team_id PK)
  ├── team_season_stats (FK: team_id, season_id)
  ├── games (FK: home_team_id, away_team_id)
  └── playoff_series (FK: home_team_id, away_team_id, winner_team_id)

seasons (season_id PK, e.g., "2023-24")
  ├── games (FK: season_id)
  ├── player_season_stats (FK: season_id)
  └── team_season_stats (FK: season_id)

playoff_series (season_id, round, series_number)
```

### API 端点设计
RESTful 风格，主要端点：

```
GET /api/v1/players                    # 球员列表（支持搜索、分页）
GET /api/v1/players/{id}               # 球员详情
GET /api/v1/players/{id}/stats         # 球员赛季统计
GET /api/v1/players/{id}/career        # 球员生涯统计

GET /api/v1/teams                      # 球队列表
GET /api/v1/teams/{id}                 # 球队详情
GET /api/v1/teams/{id}/stats           # 球队赛季统计
GET /api/v1/teams/{id}/roster          # 球队阵容
GET /api/v1/teams/{id}/games           # 球队比赛

GET /api/v1/games                      # 比赛列表（支持过滤）
GET /api/v1/games/{id}/boxscore        # 比赛 Box Score

GET /api/v1/stats/leaders              # 统计排名
GET /api/v1/stats/compare              # 球员对比

GET /api/v1/playoffs/bracket           # 季后赛对阵图
GET /api/v1/playoffs/matchups          # 历史对决
```

---

## 项目结构

```
nba-data/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/            # API 路由（players, teams, games, playoffs）
│   │   ├── core/              # 配置（config.py, database.py）
│   │   ├── models/            # SQLAlchemy 模型（8 张表）
│   │   ├── schemas/           # Pydantic schemas
│   │   └── main.py            # FastAPI 入口
│   ├── migrations/            # Alembic 迁移
│   ├── requirements.txt
│   └── alembic.ini
│
├── data/                      # 数据获取和处理
│   ├── nba_api_client/        # nba_api 封装（未使用）
│   ├── importers/             # 数据导入脚本
│   └── scripts/
│       ├── import_kaggle_data.py      # 从 Kaggle CSV 导入
│       ├── import_player_stats_v2.py  # 导入球员统计
│       ├── enrich_advanced.py         # 导入 BBR 进阶统计
│       ├── fill_playoff_series.py     # 填充季后赛系列
│       ├── fix_all_season_ids.py      # 修复 season_id 格式
│       └── fix_conference_and_query.py # 补填 conference 数据
│
├── archive/                   # Kaggle 数据集 #1（wyattowalsh）
├── archive-player/            # Kaggle 数据集 #2（eoinamoore）
├── archive-stats/             # Kaggle 数据集 #3（sumitrodatta）
│
├── analytics/                 # DuckDB 分析（待开发）
├── frontend/                  # React 前端（待开发）
├── mcp-server/                # MCP Server（待开发）
│
├── .env                       # 环境变量（数据库连接）
├── .gitignore
├── README.md
└── PROGRESS.md               # 本文件
```

---

## 下一步

### 立即可做
1. **修复 FastAPI 后端**
   - 修复 `get_db()` 同步/异步问题
   - 启动服务器并测试所有端点
   - 访问 http://localhost:8000/docs 查看 Swagger 文档

2. **前端开发**
   - 初始化 React + Vite 项目
   - 实现球员/球队查询页面
   - 集成 Recharts/D3 可视化

### 后续优化
3. **MCP Server**
   - 实现 AI Agent 工具
   - 支持自然语言查询

4. **性能优化**
   - 添加数据库索引
   - 实现查询缓存
   - 考虑 DuckDB 加速分析查询

---

## 已知问题

### 数据问题
- `teams.conference` 字段原为空，已补填 37 支球队
- `season_id` 格式混乱（`2017-18` vs `2017-20`），已统一修复
- 部分 2000 年前的赛季 ID 格式为 `YYYY-19`/`YYYY-20`（遗留格式）

### 技术问题
- FastAPI `get_db()` 同步/异步冲突（待修复）
- 未实现查询缓存
- 未添加数据库索引优化

---

## 参考资源

- [数据源研究报告](docs/research/nba-data-sources.md)
- [实施方案](.scratch/nba-database/plan.md)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org)
- [FastAPI 文档](https://fastapi.tiangolo.com)
- [PostgreSQL 文档](https://www.postgresql.org/docs/)

---

## 更新日志

### 2026-07-27
- ✅ 完成数据库设计和 8 张表填充
- ✅ 从 3 个 Kaggle 数据集导入完整数据
- ✅ 验证数据完整性（Q1、Q2 查询测试）
- ✅ 编写 FastAPI 后端路由（players, teams, games, playoffs）
- 🚧 FastAPI 后端待修复同步/异步问题
- ⏳ 前端开发未开始
- ⏳ MCP Server 未开始
