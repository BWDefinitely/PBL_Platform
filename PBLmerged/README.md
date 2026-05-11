# PBL Platform - 合并版本

本项目合并了两个后端功能：
1. **Assessment API** - 评估系统（来自 pbl--platform/assessment-api）
2. **Generator Service** - 教案生成系统（来自 pbl-platform/backend）
3. **PriorityAI** - Multi-Agent 智能优先级排序（来自 PriorityAI/）

PriorityAI 集成说明：
- 后端：`backend/src/modules/priority/`（FastAPI router + StatusAgent / TaskAgent / RankingAgent / Orchestrator），挂载在 `/api/priority/*`
- 前端：`frontend/src/pages/shared/PriorityAI.jsx`，路由 `/teacher/priority-ai` 与 `/student/priority-ai`，侧边栏已加入入口
- 原 Flask 版本（端口 5003）已转换为 FastAPI 集成至主服务（端口 8000），无需独立进程

## 项目结构

```
pbl-platform-merged/
├── backend/
│   ├── src/                    # FastAPI 主应用
│   │   ├── modules/
│   │   │   ├── assessment/     # 评估模块
│   │   │   ├── auth/           # 认证模块
│   │   │   ├── project/        # 项目模块
│   │   │   ├── report/         # 报告模块
│   │   │   └── generator/      # 教案生成模块（新增）
│   │   └── main.py             # 应用入口
│   ├── generator-service/      # 教案生成服务代码
│   └── alembic/                # 数据库迁移
└── frontend/                   # 共享前端（React + Vite）
```

## 后端功能

### Assessment API 功能
- 用户认证与授权
- 项目管理
- 评估管理
- 干预管理
- 报告生成

### Generator Service 功能
- AI 教案生成
- 逐页生成教案
- 单页重新生成
- 参考文档上传（PDF/DOCX）
- DOCX 导出

## API 端点

所有 API 端点统一在 FastAPI 应用中：

- `/api/health` - 健康检查
- `/api/auth/*` - 认证相关
- `/api/projects/*` - 项目管理
- `/api/assessments/*` - 评估管理
- `/api/reports/*` - 报告管理
- `/api/generator/*` - 教案生成（新增）
  - `POST /api/generator/generate` - 生成教案
  - `POST /api/generator/regenerate` - 重新生成单页
  - `POST /api/generator/upload-source` - 上传参考文档

## 运行方式

### 后端
```bash
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload
```

### 前端
```bash
cd frontend
npm install
npm run dev
```

