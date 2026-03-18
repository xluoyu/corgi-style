# Outfit Agent - AI 穿搭智能助手后端

基于 FastAPI + SQLAlchemy + PostgreSQL 的 AI 穿搭推荐服务后端。

## 技术栈

- **Web 框架**: FastAPI 0.109.0
- **ORM**: SQLAlchemy 2.0.25
- **数据库**: PostgreSQL + psycopg2-binary
- **环境管理**: python-dotenv

## 项目结构

```
service/
├── app/
│   ├── __init__.py
│   ├── database.py          # 数据库连接配置
│   ├── main.py              # FastAPI 应用入口
│   ├── models/              # SQLAlchemy 模型定义
│   │   ├── __init__.py
│   │   ├── clothes.py       # 衣服模型
│   │   ├── outfit.py        # 穿搭记录模型
│   │   └── user.py          # 用户模型
│   ├── routers/             # API 路由
│   │   ├── __init__.py
│   │   ├── clothes.py       # 衣服相关接口
│   │   ├── outfit.py        # 穿搭相关接口
│   │   └── user.py          # 用户相关接口
│   ├── agent/               # AI Agent 逻辑
│   │   ├── __init__.py
│   │   ├── combine_agent.py
│   │   ├── plan_agent.py
│   │   ├── short_circuit.py
│   │   ├── supervisor.py
│   │   └── tools.py
│   └── utils.py
├── schema.sql               # PostgreSQL 数据库建表语句
├── requirements.txt         # Python 依赖
├── .env.example             # 环境变量模板
└── .gitignore
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入 PostgreSQL 配置
```

**环境变量说明:**

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DB_HOST | 数据库主机 | localhost |
| DB_PORT | 数据库端口 | 5432 |
| DB_USER | 数据库用户名 | postgres |
| DB_PASSWORD | 数据库密码 | password |
| DB_NAME | 数据库名 | outfit_agent |

### 3. 初始化数据库

```bash
# 创建 PostgreSQL 数据库
psql -U postgres -f schema.sql

# 或使用 SQLAlchemy 自动创建表
python -c "from app.database import init_db; init_db()"
```

### 4. 启动服务

```bash
uvicorn app.main:app --reload
```

服务启动后访问 http://localhost:8000/docs 查看 API 文档。

## API 接口

### 用户接口 `/user`

- `POST /user/get-or-create` - 获取或创建用户
- `POST /user/update-info` - 更新用户信息
- `GET /user/preference` - 获取用户偏好

### 衣服接口 `/clothes`

- `POST /clothes/add` - 添加衣服
- `GET /clothes/list` - 获取衣服列表
- `POST /clothes/delete` - 删除衣服

### 穿搭接口 `/outfit`

- `POST /outfit/generate-today` - 生成今日穿搭
- `POST /outfit/feedback` - 提交穿搭反馈

## 数据库表结构

- **user** - 用户表
- **user_preference** - 用户偏好表
- **user_clothes** - 用户衣服表
- **outfit_record** - 穿搭记录表
- **outfit_feedback** - 穿搭反馈表

详见 [schema.sql](schema.sql)

## 部署

支持部署到任意云厂商的 PostgreSQL 服务（Supabase、Neon、阿里云、腾讯云等），只需修改 `.env` 中的数据库连接配置即可。
