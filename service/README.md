# Outfit Agent - AI 穿搭智能助手后端

基于 FastAPI + SQLAlchemy + PostgreSQL 的 AI 穿搭推荐服务后端。

## 技术栈

- **Web 框架**: FastAPI 0.109.0
- **ORM**: SQLAlchemy 2.0.25
- **数据库**: PostgreSQL + psycopg2-binary
- **AI框架**: LangChain + LangGraph
- **LLM**: 阿里云百炼 (DashScope) / OpenAI / Anthropic
- **存储**: 阿里云 OSS

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
│   │   ├── clothes_agent.py # 衣物上传 Agent (并行分析+生图)
│   │   ├── combine_agent.py
│   │   ├── plan_agent.py
│   │   ├── short_circuit.py
│   │   ├── supervisor.py
│   │   └── tools.py
│   └── services/            # 核心服务模块
│       ├── __init__.py
│       ├── image_analysis.py  # 图像分析服务 (LLM)
│       ├── image_generator.py # 图像生成服务
│       ├── llm_providers.py   # LLM Provider 抽象层
│       └── oss_uploader.py    # OSS 上传服务
├── schema.sql               # PostgreSQL 数据库建表语句
├── requirements.txt         # Python 依赖
├── .env.example             # 环境变量模板
└── .gitignore
```

## 快速开始 (Windows)

### 1. 安装依赖

```powershell
pip install -r requirements.txt
```

### 2. 配置环境变量

项目根目录已包含 `.env` 配置文件，包含数据库连接、LLM 和 OSS 的配置信息。

如需修改，编辑 `.env` 文件即可。

### 3. 启动服务

```powershell
# 进入项目目录
cd service

# 启动服务
python -m uvicorn app.main:app --reload
```

服务启动后访问 http://localhost:8000/docs 查看 API 文档。

## 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DB_HOST | 数据库主机 | localhost |
| DB_PORT | 数据库端口 | 5432 |
| DB_USER | 数据库用户名 | postgres |
| DB_PASSWORD | 数据库密码 | password |
| DB_NAME | 数据库名 | outfit_agent |

### LLM 配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| LLM_PROVIDER | LLM 提供商 | local |
| OPENAI_API_KEY | API 密钥 | - |
| OPENAI_BASE_URL | API Base URL | - |
| VISION_MODEL | 视觉分析模型 | qwen-plus |
| IMAGE_MODEL | 生图模型 | qwen-image-plus-2026-01-09 |

### OSS 配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| OSS_ENDPOINT | OSS endpoint | - |
| OSS_ACCESS_KEY_ID | Access Key ID | - |
| OSS_ACCESS_KEY_SECRET | Access Key Secret | - |
| OSS_BUCKET_NAME | Bucket 名称 | - |
| OSS_CDN_DOMAIN | CDN 域名 | - |

## API 接口

### 用户接口 `/user`

- `POST /user/get-or-create` - 获取或创建用户
- `POST /user/update-info` - 更新用户信息
- `GET /user/preference` - 获取用户偏好

### 衣服接口 `/clothes`

- `POST /clothes/add` - 添加衣服
- `POST /clothes/upload` - 上传衣服图片（AI分析+生图）
- `GET /clothes/list` - 获取衣服列表
- `POST /clothes/delete` - 删除衣服
- `GET /clothes/status/{id}` - 查询处理状态

### 穿搭接口 `/outfit`

- `POST /outfit/generate-today` - 生成今日穿搭
- `POST /outfit/feedback` - 提交穿搭反馈

## 衣物上传流程

```
POST /clothes/upload
    │
    ▼
ClothesAgent (并行执行)
    │
    ├──► analyze_clothes() ──► ImageAnalyzer ──► VL模型
    │                              ↓
    │                         提取属性
    │
    └──► generate_product_image() ──► ImageGenerator ──► 生图模型
                                        ↓
                                   标准化产品图
    │
    ▼
OSSUploader (上传OSS)
    │
    ▼
PostgreSQL (存储)
    │
    ▼
返回结果 (任一完成即返回，另一完成后异步补充)
```

### 衣物分析属性

- **color**: 颜色
- **category**: 类型 (top/pants/outer/inner/accessory)
- **material**: 材质
- **temperature_range**: 适合温度 (summer/spring_autumn/winter/all_season)
- **wear_method**: 穿着方式 (inner_wear/outer_wear/single_wear/layering)
- **scene**: 适用场景 (daily/work/sport/date/party)

## 数据库表结构

- **user** - 用户表
- **user_preference** - 用户偏好表
- **user_clothes** - 用户衣服表
- **outfit_record** - 穿搭记录表
- **outfit_feedback** - 穿搭反馈表

详见 [schema.sql](schema.sql)

## LLM Provider 架构

支持多模型接入，通过抽象接口解耦业务逻辑：

```python
# 支持的 Provider
- OpenAI (gpt-4o, etc.)
- Anthropic (claude-3, etc.)
- Local/阿里云百炼 (qwen-plus, qwen-vl, etc.)
```

切换模型只需修改 `LLM_PROVIDER` 环境变量或代码中指定 Provider。

## 部署

支持部署到任意云厂商的 PostgreSQL 服务（Supabase、Neon、阿里云、腾讯云等），只需修改 `.env` 中的数据库连接配置即可。
