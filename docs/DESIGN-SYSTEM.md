# 基金量化选基助手 - 设计系统文档

> 版本：v1.0
> 最后更新：2026-03-30
> 基于：Figma 设计 + "Digital Private Office" 理念

---

## 📋 目录

1. [设计原则](#设计原则)
2. [颜色系统](#颜色系统)
3. [字体排版](#字体排版)
4. [间距系统](#间距系统)
5. [组件规范](#组件规范)
6. [布局系统](#布局系统)
7. [动效与交互](#动效与交互)
8. [响应式设计](#响应式设计)

---

## 设计原则

### 核心理念：The Digital Private Office

我们的设计不是传统的"交易终端"，而是一个**高端私人银行空间**：
- **安静**：避免噪音和过多信息
- **权威**：通过排版和层次传达专业性
- **定制**：每个细节都经过精心设计

### 关键规则

#### 1. No-Line 规则（禁止 1px 边框）
**❌ 不要做：**
```css
border: 1px solid #ccc;
```

**✅ 要做：**
```css
/* 使用背景色区分层级 */
background-color: var(--color-surface-elevated);
/* 或者使用幽灵边框（仅在必要时） */
border: 1px solid var(--color-border); /* rgba(208, 197, 175, 0.1) */
```

#### 2. 色调分层原则
使用表面色系创建深度，而非投影：
- `--color-background` (#FBF9F8) - 基础背景
- `--color-surface` (#FFFFFF) - 卡片背景
- `--color-surface-elevated` (#F5F3F3) - 次级背景

#### 3. 不对称布局
打破传统网格，使用动态布局：
- Bento Grid 不规则网格
- 非居中对齐的强调元素
- 重叠层次创建深度

---

## 颜色系统

### 主色调

```css
/* 金色系 - 财富感 */
--color-primary: #745B00;          /* 主金色 */
--color-primary-light: #C5A021;     /* 浅金色 */
--color-primary-container: #FFE089; /* 金色容器 */
--color-on-primary: #FFFFFF;        /* 金色上的文字 */
```

**使用场景：**
- 主要操作按钮（渐变：`linear-gradient(135deg, #745B00, #C5A021)`）
- 综合评分、重要指标
- 激活状态、链接
- 图表中的积极趋势

### 次要色

```css
/* 深灰蓝 - 专业感 */
--color-secondary: #5E5E64;        /* 深灰蓝 */
--color-secondary-container: #E3E2E9; /* 次要容器 */
```

**使用场景：**
- 次要按钮
- 中性标签
- 辅助信息

### 市场语义色（A股标准）

```css
/* 中国红 - 涨/收益 */
--color-success: #BB171C;

/* 绿色 - 跌/亏损 */
--color-error: #BA1A1A;

/* 警告 - 风险提示 */
--color-warning: #F57C00;
```

**使用场景：**
- 涨跌幅：红色为正，绿色为负
- 收益率：红色为盈利，绿色为亏损
- 风险等级：R2/R3 用较浅色，R4/R5 用深色

### 表面色系

```css
/* 背景层级 */
--color-background: #FBF9F8;        /* 页面背景 */
--color-surface: #FFFFFF;           /* 卡片背景 */
--color-surface-elevated: #F5F3F3;  /* 次级背景 */
--color-surface-container: #EFECE9; /* 容器背景 */
```

**使用原则：**
- 从浅到深：Background → Surface → Elevated
- 相邻层级使用不同背景色创建边界
- 避免使用边框线

### 文本色

```css
/* 文字颜色 */
--color-text-primary: #1B1C1C;      /* 主要文字 */
--color-text-secondary: #5E5E64;    /* 次要文字 */
--color-text-muted: #7C7768;        /* 弱化文字 */
--color-text-hint: #9A9AA0;         /* 提示文字 */
```

**使用场景：**
- Primary: 标题、重要数据
- Secondary: 正文、说明
- Muted: 次要信息、时间戳
- Hint: 占位符、禁用文字

### 边框色

```css
/* 幽灵边框 - 几乎不可见 */
--color-border: rgba(208, 197, 175, 0.1);
--color-border-strong: rgba(208, 197, 175, 0.15);
```

**使用原则：**
- 仅在必要时使用（如可访问性要求）
- 优先使用背景色区分层级
- 保持"无边框"美学

---

## 字体排版

### 字体家族

```css
/* 显示字体 - 标题、强调 */
--font-family-display: 'Manrope', 'Inter', sans-serif;

/* 正文字体 - 正文、数据 */
--font-family-base: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;

/* 等宽字体 - 代码、数据 */
--font-family-mono: 'SF Mono', 'Consolas', monospace;
```

### 字号系统

```css
/* 显示级 - 财富指标 */
--text-5xl: 3.5rem;  (56px) - QUANT PICK 数值
--text-4xl: 2.5rem;  (40px) - 页面标题
--text-3xl: 2rem;    (32px) - 区块标题
--text-2xl: 1.5rem;  (24px) - 卡片标题
--text-xl: 1.25rem;  (20px) - 小标题
--text-lg: 1.125rem; (18px) - 大正文
--text-base: 1rem;   (16px) - 正文
--text-sm: 0.875rem; (14px) - 小字
--text-xs: 0.75rem;  (12px) - 标签、注释
```

### 字重

```css
/* Manrope */
font-weight: 500; /* Medium - 次要标题 */
font-weight: 600; /* SemiBold - 标题 */
font-weight: 700; /* Bold - 强调 */
font-weight: 800; /* ExtraBold - 数值 */

/* Inter */
font-weight: 400; /* Regular - 正文 */
font-weight: 500; /* Medium - 标签 */
font-weight: 600; /* SemiBold - 强调 */
```

### 排版规则

#### 标题层级
```css
/* H1 - 页面主标题 */
h1 {
  font-size: var(--text-5xl);
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1.02;
}

/* H2 - 区块标题 */
h2 {
  font-size: var(--text-4xl);
  font-weight: 700;
  letter-spacing: -0.02em;
}

/* H3 - 卡片标题 */
h3 {
  font-size: var(--text-2xl);
  font-weight: 600;
}
```

#### 数据展示
```css
/* 大数值 - 如评分、金额 */
.display-value {
  font-family: var(--font-family-display);
  font-size: var(--text-5xl);
  font-weight: 800;
  color: var(--color-primary);
}

/* 中等数值 - 如收益率 */
.metric-value {
  font-family: var(--font-family-mono);
  font-size: var(--text-lg);
  font-weight: 600;
}

/* 小数值 - 如百分比 */
.label-value {
  font-family: var(--font-family-mono);
  font-size: var(--text-sm);
}
```

#### 标签文字
```css
.label-sm {
  font-family: var(--font-family-base);
  font-size: var(--text-xs);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--color-text-secondary);
}
```

---

## 间距系统

### 基础间距

```css
--spacing-xs: 4px;    /* 0.25rem */
--spacing-sm: 8px;    /* 0.5rem */
--spacing-md: 16px;   /* 1rem */
--spacing-lg: 24px;   /* 1.5rem */
--spacing-xl: 32px;   /* 2rem */
--spacing-2xl: 40px;  /* 2.5rem */
--spacing-3xl: 48px;  /* 3rem */
```

### 使用原则

#### 组件内间距
- 卡片内边距：`--spacing-lg` (24px)
- 按钮内边距：`--spacing-sm` × `--spacing-lg` (8px × 24px)
- 表格单元格：`--spacing-md` (16px)

#### 元素间距
- 相关元素：`--spacing-sm` (8px)
- 区块间距：`--spacing-lg` (24px)
- 大区块间距：`--spacing-2xl` (40px)

#### 列表间距
- 使用 `--spacing-md` (16px) 而非分割线
- 卡片列表：交替背景色或仅间距

---

## 组件规范

### 按钮 (Button)

#### 主要按钮 (Primary)
```css
.btn-primary {
  background: linear-gradient(135deg, #745B00 0%, #C5A021 100%);
  color: #FFFFFF;
  border: none;
  border-radius: 8px;
  padding: 9px 24px;
  font-weight: 600;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(27, 28, 28, 0.08);
}
```

#### 次要按钮 (Secondary)
```css
.btn-secondary {
  background: transparent;
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 9px 24px;
  font-weight: 600;
}
```

#### 幽灵按钮 (Ghost)
```css
.btn-ghost {
  background: transparent;
  color: var(--color-text-secondary);
  border: none;
  border-radius: 8px;
  padding: 9px 16px;
}

.btn-ghost:hover {
  background: rgba(116, 91, 0, 0.08);
  color: var(--color-primary);
}
```

### 卡片 (Card)

#### 基础卡片
```css
.card {
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  overflow: hidden;
}
```

#### 填充变体
```css
.card-elevated {
  background-color: var(--color-surface-elevated);
}
```

#### 内边距规范
- 小卡片：`--spacing-md` (16px)
- 标准卡片：`--spacing-lg` (24px)
- 大卡片：`--spacing-xl` (32px)

### 标签/芯片 (Chip)

```css
.chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

/* 变体 */
.chip-neutral { background: var(--color-surface-elevated); }
.chip-gold { background: var(--color-primary-container); color: var(--color-primary); }
.chip-positive { background: rgba(187, 23, 28, 0.1); color: var(--color-success); }
.chip-negative { background: rgba(186, 26, 26, 0.1); color: var(--color-error); }
```

### 表格 (Table)

```css
.table {
  width: 100%;
  border-collapse: collapse;
}

/* 表头 - 使用背景色区分 */
.table thead {
  background-color: var(--color-surface-elevated);
}

.table th {
  padding: 16px;
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
}

.table td {
  padding: 16px;
  font-size: 14px;
}

/* 行悬停 - 使用背景色 */
.table tbody tr:hover {
  background-color: var(--color-surface-elevated);
}

/* 行分隔 - 交替背景色或仅间距 */
.table tbody tr:nth-child(even) {
  background-color: var(--color-surface-elevated);
}
```

### 输入框 (Input)

```css
.input {
  width: 100%;
  padding: 10px 16px;
  background-color: var(--color-surface-elevated);
  border: 1px solid transparent;
  border-radius: 8px;
  font-size: 14px;
  transition: all 150ms ease;
}

.input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(116, 91, 0, 0.1);
}
```

---

## 布局系统

### 网格系统

```css
/* Bento Grid - 不规则网格 */
.bento-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

/* 卡片可以跨越多列 */
.card.span-2 { grid-column: span 2; }
.card.span-3 { grid-column: span 3; }
.card.span-4 { grid-column: span 4; }
```

### 布局模式

#### 首页布局
```
┌─────────────────────────────────────────────┐
│  Header (品牌 + 导航)                        │
├─────────────────────────────────────────────┤
│  Welcome Section (标题 + 风险偏好切换)         │
├─────────────────────────────────────────────┤
│  Bento Grid (4个指标卡片)                    │
├──────────────────────────┬──────────────────┤
│  Main Content (Top10)    │  Sidebar (风险洞察) │
│  - 推荐表格               │  - 风险指标          │
│                          │  - 板块热度          │
└──────────────────────────┴──────────────────┘
```

#### 选基页布局
```
┌─────────────────────────────────────────────┐
│  Header                                      │
├──────────┬──────────────────────────────────┤
│  Filter  │  Results                          │
│  Panel   │  - Toolbar                        │
│  (292px) │  - Table                          │
│  sticky │  - Pagination                     │
└──────────┴──────────────────────────────────┘
```

#### 详情页布局
```
┌─────────────────────────────────────────────┐
│  Header (返回按钮)                           │
├─────────────────────────────────────────────┤
│  Fund Header (信息 + 评分)                   │
├──────────────────────┬───────────────────────┤
│  Main Content        │  Sidebar               │
│  - Tabs (4个)         │  - 市场数据            │
│  - Tab Content        │  - 成本信息            │
│                       │  - 快捷操作            │
└──────────────────────┴───────────────────────┘
```

### 容器

```css
.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 32px;
}

/* 页面级容器 */
.page-container {
  padding: 40px 32px 88px;
}
```

---

## 动效与交互

### 过渡时长

```css
--transition-fast: 150ms ease;   /* 微交互 */
--transition-base: 250ms ease;   /* 标准过渡 */
--transition-slow: 350ms ease;   /* 复杂动画 */
```

### 悬停效果

#### 按钮
```css
.btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}
```

#### 卡片
```css
.card:hover {
  box-shadow: var(--shadow-lg);
  /* 不要改变背景色 */
}
```

#### 表格行
```css
.table tbody tr:hover {
  background-color: var(--color-surface-elevated);
}
```

### 加载状态

#### 骨架屏
```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--color-surface-elevated) 25%,
    rgba(245, 243, 243, 0.5) 50%,
    var(--color-surface-elevated) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

#### 加载指示器
```css
.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: var(--color-text-muted);
}
```

### 空状态

```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 32px;
  color: var(--color-text-muted);
  text-align: center;
}

.empty-state-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.3;
}
```

---

## 响应式设计

### 断点

```css
/* Mobile First */
--breakpoint-sm: 640px;   /* 平板竖屏 */
--breakpoint-md: 768px;   /* 平板横屏 */
--breakpoint-lg: 1024px;  /* 桌面 */
--breakpoint-xl: 1280px;  /* 大桌面 */
```

### 响应式规则

#### 导航栏
```css
/* 桌面：完整导航 */
@media (min-width: 1024px) {
  .nav-desktop { display: flex; }
  .nav-mobile { display: none; }
}

/* 移动：汉堡菜单 */
@media (max-width: 1023px) {
  .nav-desktop { display: none; }
  .nav-mobile { display: flex; }
}
```

#### 网格布局
```css
/* 桌面：4列 */
@media (min-width: 1024px) {
  .grid-cols-4 { grid-template-columns: repeat(4, 1fr); }
}

/* 平板：2列 */
@media (min-width: 640px) and (max-width: 1023px) {
  .grid-cols-4 { grid-template-columns: repeat(2, 1fr); }
}

/* 移动：1列 */
@media (max-width: 639px) {
  .grid-cols-4 { grid-template-columns: 1fr; }
}
```

#### 字号缩放
```css
/* 使用 clamp() 实现流畅缩放 */
h1 {
  font-size: clamp(2rem, 4vw, 4rem);
}

.display-value {
  font-size: clamp(2.5rem, 5vw, 3.5rem);
}
```

---

## 设计决策记录

### 为什么不用 1px 边框？
传统 UI 使用边框线分隔内容，但这会：
1. 创造视觉噪音
2. 打断流畅性
3. 显得"廉价"

我们的方案：使用背景色和间距创建边界，更"高级"。

### 为什么用金色？
1. **财富象征**：金色在金融语境中代表价值
2. **品牌识别**：区别于通用的蓝色科技产品
3. **A 股语境**：符合中国用户对"财富"的认知

### 为什么用不对称布局？
1. **打破网格**：避免"模板感"
2. **引导视线**：不对称布局创造视觉动线
3. **定制感**：每个布局都像"精心设计"的

### 为什么用 Manrope + Inter？
1. **Manrope**：现代、几何、温暖，适合标题
2. **Inter**：技术感、可读性高，适合数据和正文
3. **搭配**：既有个性又不失专业性

---

## 扩展指南

### 添加新组件

1. **遵循现有模式**：查看类似组件的实现
2. **使用设计令牌**：不要硬编码颜色、间距
3. **保持一致性**：悬停效果、过渡时长等
4. **文档化**：更新本文档

### 添加新页面

1. **使用布局模式**：参考现有页面结构
2. **复用组件**：优先使用现有组件库
3. **响应式**：从移动端开始设计
4. **测试**：在不同断点下测试

### 调整设计令牌

如果需要调整：
1. **评估影响**：修改会影响所有使用该令牌的地方
2. **渐进迁移**：新令牌名（如 `--color-primary-v2`）
3. **更新文档**：记录变更原因
4. **团队同步**：确保所有开发者知晓

---

## 资源链接

- **Figma 设计**: [链接]
- **原型需求**: `STITCH_PROMPT.md`
- **设计理念**: `aurelian_capital/DESIGN.md`
- **产品需求**: `PRD.md`

---

*本文档由 Claude Code 维护，每次设计更新后请同步更新。*
