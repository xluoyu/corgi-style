# DIY穿搭白板功能设计文档

**版本**：v1.0
**日期**：2026-04-14
**作者**：产品团队
**状态**：待评审

---

## 一、功能概述

在白板中实现一个人形底图，用户可以通过抽屉面板选择衣物拖拽到模特的各个点位上，实现多件衣服的 DIY 叠穿搭配。最终通过 AI 生成真人模特穿着效果图。

### 核心价值
- 让用户直观地搭配衣物组合
- AI 生成真人穿着效果，降低购物决策风险
- 保存搭配记录，便于日后参考

---

## 二、页面结构

### 2.1 布局设计

```
┌─────────────────────────────────────────────────────────────────┐
│  ← DIY穿搭                                           [保存]       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────┐  ┌───────────────┐ │
│  │                                        │  │               │ │
│  │              画布区域                   │  │    抽屉面板    │ │
│  │                                        │  │               │ │
│  │         👤 人形底图                     │  │   用户衣柜    │ │
│  │                                        │  │   衣物列表    │ │
│  │    [上身点位] ← 衣物卡片叠加区域        │  │               │ │
│  │    [下身点位]                          │  │  - 分类筛选    │ │
│  │    [鞋子点位]                          │  │  - 搜索       │ │
│  │                                        │  │               │ │
│  │         📿 ← 配饰可自由拖动             │  │               │ │
│  │                                        │  │               │ │
│  └────────────────────────────────────────┘  └───────────────┘ │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  当前搭配                                                        │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                │
│  │内搭  │ │衬衫  │ │外套  │ │下身  │ │鞋子  │  +2个配饰      │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘                │
├─────────────────────────────────────────────────────────────────┤
│                      [AI生成穿搭图]                              │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 抽屉交互

- 抽屉从右侧滑出（桌面端）/ 从底部滑出（移动端）
- 支持按分类筛选：全部 / 上装 / 下装 / 鞋子 / 配饰
- 支持搜索衣物名称

---

## 三、功能定义

### 3.1 点位系统

| 点位 | 类型 | 叠加规则 | 说明 |
|------|------|----------|------|
| 上身 | 固定点位 | 可叠加多件（内搭→衬衫→外套） | 按添加顺序自动分层 |
| 下身 | 固定点位 | 单件 | 替换式添加 |
| 鞋子 | 固定点位 | 单件 | 替换式添加 |
| 配饰 | 自由区域 | 多件 | 可拖动到任意位置，记录坐标 |

### 3.2 拖拽交互

| 行为 | 结果 |
|------|------|
| 拖衣物到上身点位 | 自动叠加到上身区域 |
| 拖衣物到下身点位 | 自动替换下身现有衣物 |
| 拖衣物到鞋子点位 | 自动替换鞋子现有衣物 |
| 拖配饰到画布 | 放置在释放位置，记录坐标 |
| 点击点位衣物 | 显示操作菜单（移除/上移/下移） |

### 3.3 AI 生图

| 项目 | 说明 |
|------|------|
| 触发方式 | 手动点击「AI生成穿搭图」按钮 |
| 输入 | 衣物图片列表 + 点位信息 + 配饰位置 + 文字描述 |
| 模型 | qwen-image-2.0（通义千问图像模型） |
| 输出 | 真人模特穿着效果图 URL |

### 3.4 保存与记录

- 保存当前搭配（衣物+配饰+位置+生成图）到 DIY 记录
- 支持查看历史 DIY 记录
- 支持删除 DIY 记录

---

## 四、数据结构

### 4.1 前端状态

```typescript
// 点位衣物
interface SlotClothing {
  id: string;           // clothing_items 表的 uuid
  category: 'top' | 'bottom' | 'shoes' | 'accessory';
  imageUrl: string;
  name: string;
}

// 配饰项
interface AccessoryItem {
  id: string;
  clothing: SlotClothing;
  position: { x: number; y: number };
}

// DIY 搭配状态
interface DIYOutfitState {
  slots: {
    top: SlotClothing[];      // 上身，可多件
    bottom: SlotClothing | null;
    shoes: SlotClothing | null;
  };
  accessories: AccessoryItem[];
}
```

### 4.2 后端数据模型

```sql
CREATE TABLE diy_outfits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- 点位衣物映射（JSONB）
    -- 结构：{ "top": ["uuid1", "uuid2"], "bottom": "uuid3", "shoes": "uuid4" }
    slots JSONB NOT NULL DEFAULT '{}',

    -- 配饰列表（JSONB）
    -- 结构：[{"clothing_id": "uuid5", "position": {"x": 120, "y": 340}}, ...]
    accessories JSONB NOT NULL DEFAULT '[]',

    -- AI 生成的穿搭图
    generated_image_url TEXT,

    -- 用户补充描述
    prompt TEXT,

    -- 状态
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_diy_outfits_user_id ON diy_outfits(user_id);
CREATE INDEX idx_diy_outfits_created_at ON diy_outfits(created_at DESC);
```

### 4.3 API 接口

#### 4.3.1 生成穿搭图

```
POST /diy/generate

请求体：
{
  "slots": {
    "top": ["uuid1", "uuid2", "uuid3"],  // 上身可叠加多件
    "bottom": "uuid4",                    // 下身单件
    "shoes": "uuid5"                      // 鞋子单件
  },
  "accessories": [
    {"clothing_id": "uuid6", "position": {"x": 120, "y": 340}},
    {"clothing_id": "uuid7", "position": {"x": 80, "y": 200}}
  ],
  "prompt": "适合春日出行，休闲风格"
}

响应：
{
  "success": true,
  "image_url": "https://oss.xxx.com/diy/xxx.png"
}
```

#### 4.3.2 保存搭配

```
POST /diy/save

请求体：
{
  "name": "春日休闲穿搭",
  "slots": {
    "top": ["uuid1", "uuid2", "uuid3"],  // 上身可叠加多件
    "bottom": "uuid4",                    // 下身单件
    "shoes": "uuid5"                      // 鞋子单件
  },
  "accessories": [
    {"clothing_id": "uuid6", "position": {"x": 120, "y": 340}}
  ],
  "generated_image_url": "https://oss.xxx.com/diy/xxx.png",
  "prompt": "适合春日出行，休闲风格"
}

响应：
{
  "success": true,
  "id": "diy_uuid"
}
```

#### 4.3.3 查询记录

```
GET /diy/list
GET /diy/:id
DELETE /diy/:id
```

---

## 五、技术方案

### 5.1 技术选型

| 类别 | 技术 | 说明 |
|------|------|------|
| 画布库 | Fabric.js | 成熟稳定的 2D 画布库，支持触摸 |
| 状态管理 | React useState/useReducer | 页面级状态管理 |
| 样式 | Tailwind CSS | 与现有项目一致 |
| 动画 | Framer Motion | 与现有项目一致 |
| 生图模型 | qwen-image-2.0 | 阿里云通义千问图像模型 |

### 5.2 画布层级结构

```
Fabric.js 画布层级（从底到顶）：
┌─────────────────────────────────────┐
│  Layer 5: UI 层                      │ ← 点位气泡、操作提示
├─────────────────────────────────────┤
│  Layer 4: 配饰层                     │ ← 自由拖动的配饰
├─────────────────────────────────────┤
│  Layer 3: 衣物层                     │ ← 叠加在点位上的衣物
├─────────────────────────────────────┤
│  Layer 2: 点位标记层                  │ ← 不可见的碰撞区域
├─────────────────────────────────────┤
│  Layer 1: 背景层                     │ ← 人形底图（锁定，不可操作）
└─────────────────────────────────────┘
```

### 5.3 人形底图规格

| 项目 | 值 |
|------|-----|
| 尺寸 | 宽度 300px，高度按比例约 600px |
| 格式 | PNG 透明背景 |
| 风格 | 扁平化人形剪影，简约线条 |
| 来源 | 使用现有的 assets 或新设计 |

### 5.4 点位坐标（相对画布）

```typescript
const SLOT_POSITIONS = {
  top: { x: 150, y: 120, width: 120, height: 150 },   // 上身区域
  bottom: { x: 150, y: 280, width: 100, height: 180 }, // 下身区域
  shoes: { x: 150, y: 480, width: 80, height: 80 },    // 鞋子区域
};
```

### 5.5 AI 生图 Prompt 构建

```typescript
function buildGeneratePrompt(
  slots: DIYOutfitState['slots'],
  accessories: AccessoryItem[],
  userPrompt: string
): string {
  const parts: string[] = [];

  // 衣物描述
  if (slots.top.length > 0) {
    parts.push(`上装：${slots.top.map(c => c.name).join('、')}`);
  }
  if (slots.bottom) {
    parts.push(`下装：${slots.bottom.name}`);
  }
  if (slots.shoes) {
    parts.push(`鞋子：${slots.shoes.name}`);
  }
  if (accessories.length > 0) {
    parts.push(`配饰：${accessories.map(a => a.clothing.name).join('、')}`);
  }

  // 组合描述
  let prompt = `真人模特穿搭，${parts.join('，')}。`;
  prompt += userPrompt ? `额外要求：${userPrompt}` : '';
  prompt += '，正面站姿，简洁背景，高质量';

  return prompt;
}
```

### 5.6 衣物图片处理

1. 用户上传衣物时，系统已生成抠图后的透明背景图（`cartoon_image_url`）
2. DIY 生成时使用抠图后的图片作为输入
3. 多张图片按点位分组传入 qwen-image-2.0

---

## 六、组件设计

### 6.1 组件列表

| 组件 | 文件路径 | 职责 |
|------|---------|------|
| DIYPage | `app/src/app/diy/page.tsx` | 页面容器 |
| FabricCanvas | `app/src/components/diy/FabricCanvas.tsx` | Fabric.js 画布封装 |
| MannequinBackground | `app/src/components/diy/MannequinBackground.tsx` | 人形底图 |
| SlotZone | `app/src/components/diy/SlotZone.tsx` | 点位区域组件 |
| AccessoryItem | `app/src/components/diy/AccessoryItem.tsx` | 可拖动配饰 |
| WardrobeDrawer | `app/src/components/diy/WardrobeDrawer.tsx` | 衣柜抽屉面板 |
| ClothingCard | `app/src/components/diy/ClothingCard.tsx` | 衣物卡片 |
| OutfitSummary | `app/src/components/diy/OutfitSummary.tsx` | 搭配列表摘要 |
| GenerateButton | `app/src/components/diy/GenerateButton.tsx` | AI 生成按钮 |
| GeneratedImageModal | `app/src/components/diy/GeneratedImageModal.tsx` | 生成结果弹窗 |

### 6.2 组件关系

```
DIYPage
├── FabricCanvas
│   ├── MannequinBackground
│   ├── SlotZone (top)
│   ├── SlotZone (bottom)
│   ├── SlotZone (shoes)
│   └── AccessoryItem (multiple)
├── WardrobeDrawer
│   └── ClothingCard (draggable, multiple)
├── OutfitSummary
└── GenerateButton
    └── GeneratedImageModal
```

---

## 七、API 路由设计

### 7.1 后端路由

| 方法 | 路径 | 职责 |
|------|------|------|
| POST | `/diy/generate` | 调用 qwen-image-2.0 生成穿搭图 |
| POST | `/diy/save` | 保存 DIY 搭配 |
| GET | `/diy/list` | 获取用户 DIY 记录列表 |
| GET | `/diy/:id` | 获取单条 DIY 记录详情 |
| DELETE | `/diy/:id` | 删除 DIY 记录 |

### 7.2 生图服务

```python
# service/app/services/image_generator_v2.py

async def generate_outfit_image(
    clothes_images: List[str],  # 衣物图片 URL 列表
    accessories: List[dict],    # 配饰信息含位置
    prompt: str                 # 描述 prompt
) -> str:
    """
    调用 qwen-image-2.0 生成穿搭图
    返回生成图片的 URL
    """
    # 1. 预处理：将衣物图片上传到可访问的 OSS 地址
    # 2. 构建多模态 prompt
    # 3. 调用 qwen-image-2.0 API
    # 4. 下载生成的图片
    # 5. 上传到 OSS
    # 6. 返回 URL
```

---

## 八、移动端适配

| 场景 | 适配方案 |
|------|----------|
| 抽屉 | 从底部滑出，半屏弹窗 |
| 画布 | 宽度 100%，高度自适应 |
| 触摸拖拽 | Fabric.js 内置触摸支持 |
| 点位点击 | 增大点击热区到 44px 以上 |

---

## 九、开发工作量

| 模块 | 工作量 | 优先级 |
|------|--------|--------|
| Fabric.js 画布封装 | 中 | P0 |
| 人形底图设计 | 低 | P0 |
| 点位系统实现 | 中 | P0 |
| 衣物拖拽交互 | 中 | P0 |
| 配饰自由拖动 | 低 | P0 |
| 衣柜抽屉面板 | 低 | P0 |
| 搭配列表展示 | 低 | P0 |
| 后端 DIY API | 中 | P0 |
| qwen-image-2.0 对接 | 高 | P0 |
| DIY 记录列表页 | 中 | P1 |
| 移动端适配优化 | 中 | P1 |

---

## 十、风险与应对

| 风险 | 等级 | 应对方案 |
|------|------|----------|
| qwen-image-2.0 生图可控性 | 🔴 高 | 文字描述指定场景/风格；多图输入作为参考 |
| 衣物融合质量 | 🔴 高 | 使用抠图后的透明背景图；模型选择合适的 task_type |
| 移动端拖拽精度 | 🟡 中 | 增大点位热区；提供微调功能 |
| 画布性能 | 🟡 中 | 限制衣物数量；优化重绘策略 |

---

## 十一、后续扩展

- [ ] AI 推荐搭配：根据天气、场景自动推荐点位衣物
- [ ] 穿搭评分：AI 对搭配效果打分
- [ ] 分享功能：生成分享链接/海报
- [ ] 历史对比：对比不同搭配的效果

---

## 附录

### A. 现有相关文件

| 文件 | 说明 |
|------|------|
| `service/schema.sql` | 数据库 Schema |
| `service/app/models/clothes.py` | 衣物数据模型 |
| `app/src/types/api.ts` | 前端 API 类型 |
| `app/src/lib/api/clothes.ts` | 衣物 API 调用 |

### B. 环境变量

| 变量名 | 说明 |
|--------|------|
| `QWEN_IMAGE_API_KEY` | qwen-image-2.0 API 密钥 |
| `QWEN_IMAGE_API_URL` | qwen-image-2.0 API 地址 |
