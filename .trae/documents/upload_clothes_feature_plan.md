# 相册上传衣物功能实施计划

## 需求概述
将上传衣物功能从 /wardrobe 页面移动到 TabBar 右侧按钮的弹窗中，实现「相册上传」功能。

## 实施步骤

### 1. 修改前端 BottomNav 组件
- 在右侧添加按钮的弹窗菜单中新增「相册上传」选项（需要添加图标）
- 移除现有的「复制链接」选项（按需求保留三个选项：拍照上传、相册上传、链接上传）
- 点击「相册上传」时触发隐藏的文件选择器

### 2. 修改前端 wardrobe 页面
- 移除页面中的上传按钮（红色圆形 + 按钮）
- 移除上传模态框
- 保留衣物列表展示逻辑
- 修改衣物列表项的展示：当 `analysis_completed` 为 false 时，显示"识别中..."文字

### 3. 后端新增 API 接口
- 新增 `POST /clothes/upload-simple` 接口
- 接收图片文件，上传到 OSS
- 保存衣物记录到数据库，字段初始值：
  - `description`: "识别中..."
  - `color`: "识别中..."
  - `material`: "识别中..."
  - `category`: "top" (默认值)
  - `temperature_range`: "all_season"
  - `analysis_completed`: false
  - `generated_completed`: false
- 异步触发 clothes_agent 进行分析和生成商品图
- 返回成功标识给前端

### 4. 修改前端 API 客户端
- 新增 `uploadClothesImageSimple` 函数
- 处理文件上传并显示 toast

### 5. 前端页面优化
- 修改 wardrobe 页面衣物展示：显示原始图片 + "识别中..."状态
- 确保下次访问页面时从数据库拉取最新数据（已实现）

## 文件修改清单

| 文件 | 修改内容 |
|------|----------|
| `app/src/components/BottomNav.tsx` | 添加相册上传选项和逻辑 |
| `app/src/app/wardrobe/page.tsx` | 移除上传按钮，修改衣物展示逻辑 |
| `app/src/lib/api.ts` | 新增 uploadClothesImageSimple 函数 |
| `service/app/routers/clothes.py` | 新增 upload-simple API 接口 |
| `service/app/models/clothes.py` | 添加 analysis_completed 和 generated_completed 字段 |

## 预期效果
1. 用户点击 TabBar 右侧 + 按钮，弹出三个选项
2. 用户选择「相册上传」，打开系统相册
3. 选择图片后显示「上传中...」toast
4. 后端上传图片到 OSS 并保存记录（状态为"识别中..."）
5. 前端跳转到 /wardrobe 页面，显示新上传的衣物图片和"识别中..."状态
6. 后台异步处理分析和商品图生成，下次访问时显示完整信息
