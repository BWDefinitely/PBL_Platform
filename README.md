# PBL 智教平台

基于 AI 的项目式学习（PBL）教学支持平台，集成教学方案生成、过程数据采集、智能评估、决策支持与测试数据生成等功能。

## 项目结构

```
PBL_Platform/
├── backend/
│   ├── src/                        # FastAPI 主应用
│   │   ├── modules/
│   │   │   ├── auth/               # 用户认证与授权
│   │   │   ├── project/            # 项目与干预管理
│   │   │   ├── assessment/         # 评估管理
│   │   │   ├── report/             # 报告生成
│   │   │   ├── generator/          # AI 教案生成
│   │   │   ├── priority/           # 任务优先级排序（AI Agent）
│   │   │   └── autogen/            # 多智能体对话数据生成（测试专属）
│   │   ├── core/                   # 核心配置
│   │   ├── db/                     # 数据库会话
│   │   ├── models/                 # SQLAlchemy 模型
│   │   └── main.py                 # 应用入口
│   ├── generator-service/          # 教案生成服务实现
│   ├── autogen/                    # AutoGen 多智能体群聊数据生成器
│   │   ├── src/                    # 生成器核心代码
│   │   ├── configs/                # 实验配置
│   │   ├── runs/                   # 运行结果保存目录（每次运行独立子目录）
│   │   ├── _run_entry.py           # 进程入口包装器（过滤日志噪音）
│   │   ├── run_timeline_experiments.py
│   │   └── run_experiments.py
│   ├── llm_config.json             # 统一 LLM API 配置（唯一真实源）
│   ├── alembic/                    # 数据库迁移
│   └── requirements.txt
└── frontend/                       # React + Vite 前端
    ├── src/
    │   ├── pages/
    │   │   ├── teacher/            # 教师端页面
    │   │   └── student/            # 学生端页面
    │   ├── components/             # 共享组件
    │   └── context/                # 全局状态
    └── package.json
```

## 核心功能

### 教师端
- **项目总览** — 项目进度、学生状态、关键指标
- **教学方案生成** — AI 驱动的 PBL 教案生成（支持参考文档上传、逐页生成、单页重新生成、DOCX 导出）
- **任务与进度管理** — 任务分配、进度跟踪、AI 优先级排序
- **过程数据采集** — 学生行为、协作、产出物记录
- **AI 过程评估** — 基于过程数据的智能评估
- **决策支持中心** — 干预建议、风险预警
- **AI 生成数据（测试）** — 多智能体群聊数据生成器，用于模拟学生团队对话（测试专属）

### 学生端
- **项目概览** — 任务列表、截止日期、团队成员
- **我的任务** — 任务详情、提交状态
- **任务进度** — 可视化进度跟踪
- **团队讨论** — 实时协作聊天
- **文件管理** — 文档上传与共享
- **能力报告** — 个人能力画像
- **我的画像** — 学习轨迹与成长记录

## API 端点

所有 API 端点统一在 FastAPI 应用中（默认端口 8100）：

| 路径 | 功能 |
|------|------|
| `/api/health` | 健康检查 |
| `/api/auth/*` | 用户认证、注册、登录、Token 刷新 |
| `/api/projects/*` | 项目 CRUD、成员管理 |
| `/api/interventions/*` | 干预记录管理 |
| `/api/assessments/*` | 评估管理、结果查询 |
| `/api/reports/*` | 报告生成与导出 |
| `/api/generator/*` | AI 教案生成、重新生成、参考文档上传 |
| `/api/priority/*` | AI Agent 任务优先级排序 |
| `/api/autogen/*` | 多智能体对话数据生成（测试专属）：运行任务、浏览/下载结果、取消/删除任务 |

## LLM 配置

**所有 LLM API 配置集中在一个文件：`backend/llm_config.json`**

```json
{
  "platform": {
    "model": "gpt-5.4-nano",
    "api_key": "sk-...",
    "base_url": "https://jeniya.cn/v1"
  },
  "dialogue":  [ { "model": "...", "api_key": "...", "base_url": "..." } ],
  "controller":[ { "model": "...", "api_key": "...", "base_url": "..." } ]
}
```

- `platform` — generator-service 等单模型场景使用
- `dialogue` / `controller` — autogen 多智能体场景使用（对话模型 / 控制器模型）

修改这一个文件即可同步整个平台的模型/密钥/端点。环境变量（`JENIYA_API_KEY` / `JENIYA_BASE_URL` / `JENIYA_MODEL`）仍然优先，可用于部署时覆盖。

## 快速开始

### 1. 安装依赖

**后端**
```bash
cd backend
pip install -r requirements.txt
```

**前端**
```bash
cd frontend
npm install
```


### 2. 配置 LLM API

编辑 `backend/llm_config.json`，填入你的 API Key 和端点。

### 3. 启动服务

**后端**
```bash
cd backend
uvicorn src.main:app --reload 
```

**前端**
```bash
cd frontend
npm run dev
```

前端默认运行在 `http://localhost:5173`，后端 API 在 `http://localhost:8000`。

### 4. 访问平台

打开浏览器访问 `http://localhost:5173`，注册账号后即可使用。

## 数据库

- 默认使用 SQLite（`backend/assessment_api.db`）
- 生产环境可通过 `backend/src/core/config.py` 中的 `database_url` 切换到 PostgreSQL / MySQL
- 迁移由 Alembic 管理（`backend/alembic/`）

## 开发说明

### 添加新模块

1. 在 `backend/src/modules/` 下创建新模块目录
2. 实现 `router.py`（FastAPI APIRouter，带 `prefix="/api/xxx"`）
3. 在 `backend/src/main.py` 中注册路由：
   ```python
   from src.modules.your_module.router import router as your_router
   app.include_router(your_router)
   ```

### 前端路由

- 教师端路由：`/teacher/*`
- 学生端路由：`/student/*`
- 路由定义在 `frontend/src/App.jsx`
- 侧边栏导航在 `frontend/src/components/Sidebar.jsx`

### AutoGen 数据生成器

测试专属功能，用于生成模拟学生团队对话数据：

- 每次运行保存到 `backend/autogen/runs/<job_id>/`，分为 `logs/`（运行日志）和 `data/`（生成数据）两个子目录
- 前端入口：教师端侧边栏 → "AI 生成数据（测试）"
- 支持模式：`timeline_v2`（推荐）/ `legacy`
- 可选参数：`smoke-test`（短程测试）、`dry-run`（仅校验配置）、`estimate-cost`（估算 token 用量）
- 支持中途取消（已生成的部分会保留在硬盘上）、删除任务、浏览/下载/在资源管理器中定位结果
- 浏览器仅暴露 `runs/` 目录，不会泄露源码或配置
- 运行日志已过滤 AutoGen 的 pricing warning，不会污染对话数据

## 技术栈

- **后端**: FastAPI, SQLAlchemy, Alembic, Pydantic, AutoGen 0.2
- **前端**: React 18, React Router, Vite
- **AI**: OpenAI-compatible API（支持第三方代理如 Jeniya）
- **数据库**: SQLite（开发）/ PostgreSQL（生产）
