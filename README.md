# Corgi Style - AI 穿搭智能助手

前后端分离的 AI 穿搭推荐应用，基于 FastAPI + React。

## 项目结构

```
Corgi-style/
├── app/                    # 前端 (React + Vite + TailwindCSS)
│   ├── src/
│   │   ├── pages/          # 页面组件
│   │   │   ├── HomePage.tsx
│   │   │   ├── WardrobePage.tsx
│   │   │   └── ProfilePage.tsx
│   │   ├── styles/         # 样式文件
│   │   ├── lib/           # 工具函数
│   │   └── App.tsx
│   ├── dist/              # 构建输出
│   └── package.json
├── service/                # 后端 (FastAPI + SQLAlchemy + PostgreSQL)
│   ├── app/
│   │   ├── models/        # 数据库模型
│   │   ├── routers/       # API 路由
│   │   └── agent/         # AI Agent 逻辑
│   ├── schema.sql         # PostgreSQL 建表语句
│   ├── requirements.txt   # Python 依赖
│   └── .env.example       # 环境变量模板
├── design/                # 设计规范与组件库
└── docs/                  # 产品文档
```

## 技术栈

### 前端
- React 18 + TypeScript
- Vite 6
- TailwindCSS 4
- Radix UI 组件
- Framer Motion 动画

### 后端
- FastAPI 0.109
- SQLAlchemy 2.0
- PostgreSQL + psycopg2-binary
- python-dotenv

## 快速开始

### 前端

```bash
cd app
npm install
npm run dev
```

### 后端

```bash
cd service
pip install -r requirements.txt
cp .env.example .env  # 配置数据库
psql -U postgres -f schema.sql  # 初始化数据库
uvicorn app.main:app --reload
```

## 环境变量

后端 `.env` 配置:

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DB_HOST | 数据库主机 | localhost |
| DB_PORT | 数据库端口 | 5432 |
| DB_USER | 数据库用户名 | postgres |
| DB_PASSWORD | 数据库密码 | password |
| DB_NAME | 数据库名 | outfit_agent |

## API 接口

### 用户 `/user`
- `POST /user/get-or-create` - 获取或创建用户
- `POST /user/update-info` - 更新用户信息
- `GET /user/preference` - 获取用户偏好

### 衣服 `/clothes`
- `POST /clothes/add` - 添加衣服
- `GET /clothes/list` - 获取衣服列表
- `POST /clothes/delete` - 删除衣服

### 穿搭 `/outfit`
- `POST /outfit/generate-today` - 生成今日穿搭
- `POST /outfit/feedback` - 提交穿搭反馈

详细 API 文档: http://localhost:8000/docs
