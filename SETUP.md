# NBA 历史数据库搭建指南

> 最后更新：2026-07-27

## 概述

构建完整的本地 NBA 历史数据库（1946 年至今约 80 年），支持数据分析、Web API 和 AI Agent 集成。

## 技术栈

| 组件 | 选型 | 理由 |
|------|------|------|
| 数据库 | PostgreSQL 17 | 支持复杂查询、并发 |
| 分析引擎 | DuckDB | 列式存储，10-100x 加速 |
| Web 框架 | FastAPI | 现代异步框架 |
| 数据源 | Kaggle 数据集 ×3 | 替代被封锁的 nba_api |

## 为什么没用 nba_api

nba_api 在 2024-2025 年被 stats.nba.com 的 Akamai TLS 指纹识别拦截，即使挂代理也无法获取 JSON 数据（返回 HTML）。改用 Kaggle 离线数据集。

## 使用的 3 个 Kaggle 数据集

### 1. NBA Database (wyattowalsh)

- **下载链接**: https://www.kaggle.com/datasets/wyattowalsh/basketball
- **格式**: SQLite / CSV
- **大小**: ~2.3GB
- **内容**: 球员基本信息、球队信息、比赛记录、每节比分、Play-by-Play
- **覆盖**: 1946-47 至今，每日更新
- **解压到**: `archive/`

### 2. NBA Dataset: Box Scores and Stats (eoinamoore)

- **下载链接**: https://www.kaggle.com/datasets/eoinamoore/historical-nba-data-and-player-box-scores
- **格式**: CSV / Parquet
- **大小**: ~1.3GB
- **内容**: 球员单场 Box Score、球队统计、进阶统计（ORtg/DRtg/TS%/USG%/PIE 等）
- **覆盖**: 1947 至今，持续维护
- **解压到**: `archive-player/`

### 3. NBA Stats (1947-present) (sumitrodatta)

- **下载链接**: https://www.kaggle.com/datasets/sumitrodatta/nba-aba-baa-stats
- **格式**: CSV
- **大小**: ~20MB
- **内容**: Basketball-Reference 专属进阶统计（PER/WS/BPM/VORP）、季后赛统计、球队赛季总结
- **覆盖**: 1947 至今，持续更新
- **解压到**: `archive-stats/`

## 数据量

| 表 | 记录数 |
|---|--------|
| players | 6,694 |
| teams | 91 |
| games | 75,218 |
| player_game_stats | 1,560,532 |
| player_season_stats | 27,904 (含 PER/TS%/WS/BPM/VORP) |
| playoff_series | 1,369 |

## 搭建步骤

### 1. 环境
```powershell
conda create -n nba-data python=3.11 -y
conda activate nba-data
pip install -r backend/requirements.txt
```

### 2. 数据库
```sql
CREATE DATABASE nba_data;
```
```powershell
cp .env.example .env  # 编辑数据库连接信息
cd backend && alembic upgrade head
```

### 3. 下载 Kaggle 数据集
下载上面 3 个数据集，分别解压到 `archive/`、`archive-player/`、`archive-stats/`

### 4. 导入数据
```powershell
python data/scripts/import_kaggle_data.py
python data/scripts/import_player_stats_v2.py
python data/scripts/enrich_advanced.py
python data/scripts/fill_playoff_series.py
python data/scripts/fix_all_season_ids.py
python data/scripts/fix_conference_and_query.py
```

### 5. 启动 API
```powershell
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
访问 http://localhost:8000/docs

## API 端点

- GET /api/v1/players - 球员搜索
- GET /api/v1/players/{id}/stats - 赛季统计
- GET /api/v1/teams - 球队列表
- GET /api/v1/games - 比赛查询
- GET /api/v1/games/{id}/boxscore - Box Score
- GET /api/v1/stats/leaders - 统计排名
- GET /api/v1/stats/compare - 球员对比
- GET /api/v1/playoffs/bracket - 季后赛对阵
- GET /api/v1/playoffs/matchups - 历史对决

## 参考

- [数据源研究](docs/research/nba-data-sources.md)
- [项目进度](PROGRESS.md)
- [FastAPI 文档](https://fastapi.tiangolo.com)
