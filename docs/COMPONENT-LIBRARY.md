# 组件库文档 (Component Library)

> 版本：v1.0
> 最后更新：2026-03-30

---

## 📚 目录

1. [布局组件](#布局组件)
2. [数据展示组件](#数据展示组件)
3. [表单组件](#表单组件)
4. [反馈组件](#反馈组件)
5. [导航组件](#导航组件)
6. [页面组件](#页面组件)

---

## 布局组件

### Header / 顶部导航栏

**文件**: `components/layout/Header.tsx`

**组件**:
- `TopNavigation` - 顶部导航容器
- `Brand` - 品牌标识
- `Navigation` - 导航菜单

**使用示例**:
```tsx
import { TopNavigation, Brand, Navigation } from '@/components/layout/Header';

<TopNavigation>
  <Brand />
  <Navigation
    items={[
      { label: '首页', active: true, onClick: () => {} },
      { label: '选基', active: false, onClick: () => {} },
    ]}
  />
</TopNavigation>
```

**Props**:
```typescript
interface NavItem {
  label: string;
  active?: boolean;
  onClick?: () => void;
}

// Navigation
interface NavigationProps {
  items: NavItem[];
}
```

**样式规范**:
- 高度：64px
- 内边距：0 32px
- 背景色：`--color-background`
- 激活状态：金色下划线 (2px)

---

## 数据展示组件

### MetricCard / 指标卡片

**文件**: `components/dashboard/MetricCard.tsx`

**用途**: 展示关键指标（如推荐数量、预警数、市场温度）

**变体**:
- `default` - 默认（白色背景）
- `gold` - 金色强调（底部金色边框）
- `red` - 红色警告（底部红色边框）

**使用示例**:
```tsx
<MetricCard
  label="QUANT PICK"
  value="10 只"
  note="今日模型优选推荐"
  variant="gold"
  action={<button>刷新</button>}
/>
```

**Props**:
```typescript
interface MetricCardProps {
  label: string;        // 标签（小字）
  value: string | number; // 数值（大字）
  note?: string;        // 说明文字
  icon?: ReactNode;     // 图标
  action?: ReactNode;   // 操作按钮
  variant?: 'default' | 'gold' | 'red';
}
```

**样式规范**:
- 内边距：24px
- 最小高度：150px
- 数值字号：58px, font-weight: 800
- 布局：flex column, justify-between

---

### RecommendationTable / 推荐表格

**文件**: `components/dashboard/RecommendationTable.tsx`

**用途**: 展示基金推荐列表，支持排序和操作

**使用示例**:
```tsx
<RecommendationTable
  funds={funds}
  loading={false}
  onViewDetail={(code) => navigate(`/detail/${code}`)}
  onAddToWatchlist={(code) => addToWatchlist(code)}
/>
```

**Props**:
```typescript
interface Fund {
  code: string;
  name: string;
  type: string;
  score: number;
  riskLevel: string;
  oneYearReturn?: number;
  maxDrawdown?: number;
}

interface RecommendationTableProps {
  funds: Fund[];
  loading?: boolean;
  onViewDetail?: (code: string) => void;
  onAddToWatchlist?: (code: string) => void;
}
```

**列定义**:
1. 基金代码/名称
2. 类型（芯片）
3. 综合评分（金色大字）
4. 风险等级（芯片）
5. 近1年收益（红/绿色）
6. 最大回撤（红色）
7. 操作（详情 + 收藏按钮）

**样式规范**:
- 表头背景：`--color-surface-elevated`
- 悬停行背景：`--color-surface-elevated`
- 评分字号：32px, font-weight: 800, 金色

---

### RiskInsight / 风险洞察

**文件**: `components/dashboard/RiskInsight.tsx`

**组件**:
- `RiskInsight` - 风险透视卡片
- `SectorHeat` - 板块热度卡片

**使用示例**:
```tsx
<RiskInsight
  metrics={[
    { label: '市场波动率', value: '18.5% 偏高', tone: 'negative' },
    { label: '信用利差', value: '0.42% 稳定', tone: 'neutral' },
  ]}
  callout={{
    label: '智能调仓提示',
    value: '当成长拥挤度偏高时，优先保留抗回撤更均衡的标的。',
  }}
  extraContent={<button>生成风险报告</button>}
/>

<SectorHeat label="半导体" value="+2.45%" rise />
```

**Props**:
```typescript
interface InsightItem {
  label: string;
  value: string;
  tone?: 'neutral' | 'positive' | 'negative';
}

interface Callout {
  label: string;
  value: string;
}

interface RiskInsightProps {
  metrics?: InsightItem[];
  callout?: Callout;
  extraContent?: ReactNode;
}

interface SectorHeatProps {
  label: string;
  value: string;
  rise?: boolean;
}
```

**样式规范**:
- 指标项：背景 `--color-surface-elevated`, padding 12px, 圆角 8px
- Callout: 背景 #F6EFCF, 文字 #483800
- SectorHeat: 上升用 #FFEFED, 下跌用 #EEF8F2

---

## 表单组件

### Input / 输入框

**CSS 类**: `.input`

**使用示例**:
```tsx
<input
  type="text"
  className="input"
  placeholder="代码/简称/经理"
  value={keyword}
  onChange={(e) => setKeyword(e.target.value)}
/>
```

**变体**:
- 默认：浅灰背景
- 聚焦：金色边框 + 外阴影
- 错误：红色边框（待实现）

**样式规范**:
```css
.input {
  padding: 10px 16px;
  background: var(--color-surface-elevated);
  border: 1px solid transparent;
  border-radius: 8px;
  font-size: 14px;
}

.input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(116, 91, 0, 0.1);
}
```

---

### Button / 按钮

**CSS 类**: `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-ghost`

**使用示例**:
```tsx
<button className="btn btn-primary">主要操作</button>
<button className="btn btn-secondary">次要操作</button>
<button className="btn btn-ghost">幽灵按钮</button>
```

**尺寸规范**:
- 内边距：9px 24px（标准）
- 小按钮：padding 6px 12px
- 圆角：8px

**状态**:
- 默认：正常显示
- 悬停：上移 1px + 阴影
- 禁用：opacity 0.5

---

### Chip / 标签芯片

**CSS 类**: `.chip`, `.chip-neutral`, `.chip-gold`, `.chip-positive`, `.chip-negative`

**使用示例**:
```tsx
<span className="chip chip-neutral">宽基</span>
<span className="chip chip-gold">高流动性</span>
<span className="chip chip-positive">+2.45%</span>
<span className="chip chip-negative">-1.12%</span>
```

**尺寸规范**:
- 内边距：4px 10px
- 圆角：999px（完全圆角）
- 字号：12px
- 字重：600

**使用场景**:
- `chip-neutral`: 基金类型、渠道
- `chip-gold`: 高流动性、VIP 状态
- `chip-positive`: 正收益、利好
- `chip-negative`: 负收益、利空、高风险

---

## 反馈组件

### Loading / 加载状态

**CSS 类**: `.loading`

**使用示例**:
```tsx
<div className="loading">加载中...</div>
```

**样式规范**:
```css
.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: var(--color-text-muted);
}
```

---

### EmptyState / 空状态

**CSS 类**: `.empty-state`

**使用示例**:
```tsx
<div className="empty-state">
  <div className="empty-state-icon">📭</div>
  <p>暂无推荐数据</p>
  <button className="btn btn-primary mt-md">重新加载</button>
</div>
```

**样式规范**:
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

### ErrorBanner / 错误横幅

**使用示例**:
```tsx
{error && (
  <div
    style={{
      padding: '14px 18px',
      margin: '0 32px 16px',
      borderRadius: '16px',
      backgroundColor: '#FFDAD6',
      color: '#93000A',
    }}
  >
    错误：{error}
  </div>
)}
```

**样式规范**:
- 背景：#FFDAD6
- 文字：#93000A
- 圆角：16px
- 内边距：14px 18px

---

## 导航组件

### Navigation / 导航菜单

**文件**: `components/layout/Header.tsx`

**使用示例**:
```tsx
<Navigation
  items={[
    { label: '首页', active: true, onClick: () => setPage('首页') },
    { label: '选基', active: false, onClick: () => setPage('选基') },
  ]}
/>
```

**样式规范**:
- 激活项：金色文字 + 金色下划线（2px）
- 非激活项：灰色文字 + 透明下划线
- 间距：20px
- 字号：15px
- 字重：600

---

## 页面组件

### HomePage / 首页

**文件**: `pages/HomePage.tsx`

**布局结构**:
1. Welcome Section（标题 + 风险偏好切换）
2. Bento Grid（4个指标卡片）
3. Main Content（Top10 推荐）
4. Sidebar（风险洞察）

**Props**:
```typescript
interface HomePageProps {
  riskProfile: '保守' | '均衡' | '进取';
  onRiskProfileChange: (profile: RiskProfile) => void;
  funds: FundScore[];
  loading?: boolean;
  onRefreshMarket?: () => void;
  refreshingMarket?: boolean;
  onViewDetail?: (code: string) => void;
  onAddToWatchlist?: (code: string) => void;
}
```

---

### PickerPage / 选基页

**文件**: `pages/PickerPage.tsx`

**布局结构**:
- 左侧：Filter Panel（292px 宽，sticky）
- 右侧：Results（flex 1）
  - Toolbar（因子权重模板 + 操作按钮）
  - Table（结果表格）

**筛选器字段**:
- 关键词搜索
- 交易渠道（场内/场外）
- 基金类别（宽基/行业/债券/混合）
- 成立年限
- 最高费率

---

### DetailPage / 详情页

**文件**: `pages/DetailPage.tsx`

**布局结构**:
1. Fund Header（返回 + 基金信息 + 评分）
2. Main Content（左侧，1.6fr）
   - Tabs（表现/因子/成本/解释）
   - Tab Content
3. Sidebar（右侧，0.9fr）
   - 市场数据
   - 成本信息
   - 快捷操作

**Tabs**:
1. **表现分析**: 收益曲线、回撤曲线、关键指标卡片
2. **因子分析**: 因子条形图（10个因子）
3. **成本与交易**: 费率、流动性、跟踪误差
4. **推荐理由**: 加分项、扣分项、免责声明

---

### ComparePage / 对比页

**文件**: `pages/ComparePage.tsx`

**布局结构**:
1. Header（标题 + 操作按钮）
2. Comparison Cards（并排对比，2列网格）
3. Comparison Tables（因子对比 + 成本对比）
4. Conclusion（智能结论卡片）

**对比维度**:
- 综合评分
- 收益能力
- 风险控制
- 政策支持
- 成本与流动性

---

### WatchlistPage / 观察池

**文件**: `pages/WatchlistPage.tsx`

**布局结构**:
1. Header（标题 + 操作按钮）
2. Hero Metrics（3个指标卡片）
3. Watchlist Grid（2列网格）
   - Watch Cards（带预警、趋势图）
   - Add Card（虚线边框）
4. Bottom Section（最近浏览 + 量化观察）

**Watch Card 功能**:
- 风险预警标签
- 实时量化分
- Sparkline（迷你趋势图）
- 市场行情
- 操作（详情/对比/删除）

---

## 组件开发规范

### 命名规范

**文件命名**:
- 组件：PascalCase（如 `MetricCard.tsx`）
- 工具函数：camelCase（如 `formatNumber.ts`）
- 常量：UPPER_SNAKE_CASE（如 `API_ENDPOINTS.ts`）
- 类型：PascalCase（如 `FundTypes.ts`）

**组件命名**:
- 使用描述性名称（如 `RecommendationTable` 而非 `Table1`）
- 避免缩写（如 `Watchlist` 而非 `Watch`）
- 保持一致性

### 组件结构

```tsx
// 1. Imports
import { useState } from 'react';

// 2. Types/Interfaces
interface ComponentProps {
  // ...
}

// 3. 子组件
function SubComponent() {
  // ...
}

// 4. 主组件
export function Component({ prop1, prop2 }: ComponentProps) {
  // 5. Hooks
  const [state, setState] = useState();

  // 6. Effects
  useEffect(() => {
    // ...
  }, []);

  // 7. Handlers
  function handleClick() {
    // ...
  }

  // 8. Render
  return (
    <div>
      {/* JSX */}
    </div>
  );
}
```

### Props 设计原则

1. **必需 vs 可选**: 明确标记 `?`
2. **默认值**: 提供合理的默认值
3. **类型安全**: 使用 TypeScript 接口
4. **文档化**: 复杂 props 添加注释

```typescript
interface GoodProps {
  /** 必需 */
  id: string;

  /** 可选，有默认值 */
  size?: 'small' | 'medium' | 'large';

  /** 可选，有默认值 */
  disabled?: boolean;

  /** 复杂对象添加说明 */
  config?: {
    /** 配置项说明 */
    threshold: number;
  };
}
```

### 样式原则

1. **优先使用 CSS 类**: 通过 `className` 应用样式
2. **内联样式用于**: 动态值（如宽度、颜色）、组件特有样式
3. **使用设计令牌**: 不硬编码颜色、间距
4. **保持简洁**: 避免过度嵌套

```tsx
// ✅ 好
<div className="card p-md">
  <h1 className="headline-md">标题</h1>
</div>

// ❌ 差
<div style={{ backgroundColor: '#fff', padding: '24px' }}>
  <h1 style={{ fontSize: '24px', fontWeight: 700 }}>标题</h1>
</div>
```

### 性能优化

1. **使用 React.memo**: 对于纯展示组件
2. **避免不必要渲染**: 使用 `useCallback`, `useMemo`
3. **列表渲染**: 提供 `key` prop
4. **代码分割**: 使用 `React.lazy()` + `Suspense`

```tsx
// 列表渲染
{funds.map((fund) => (
  <FundCard key={fund.code} fund={fund} />
))}

// 代码分割
const DetailPage = React.lazy(() => import('./pages/DetailPage'));

<Suspense fallback={<Loading />}>
  <DetailPage />
</Suspense>
```

---

## 扩展指南

### 添加新组件

1. **确定需求**: 这个组件解决什么问题？
2. **查看现有**: 是否有类似组件可以复用？
3. **设计 API**: Props 接口、使用方式
4. **实现组件**: 遵循组件结构规范
5. **编写文档**: 更新本文档
6. **编写测试**: 单元测试、集成测试

### 添加新变体

1. **评估影响**: 是否需要新变体？还是可以通过 props 控制？
2. **命名规范**: 使用描述性名称（如 `btn-large`, `btn-ghost`）
3. **保持一致**: 遵循现有样式规范
4. **更新文档**: 记录新变体的使用场景

### 组件维护

1. **定期审查**: 每季度检查组件使用情况
2. **废弃警告**: 使用 `@deprecated` 标记
3. **版本管理**: 重大变更时更新版本号
4. **迁移指南**: 提供升级路径

---

## 常见问题

### Q: 如何自定义组件样式？

A: 使用 `className` 覆盖，或通过 props 传递样式：

```tsx
// 方式1: className 覆盖
<Card className="custom-card" />

// 方式2: style prop
<Card style={{ marginTop: '24px' }} />

// 方式3: 支持 variant
<Card variant="elevated" />
```

### Q: 组件不支持我需要的场景怎么办？

A: 三个选择：
1. **扩展现有组件**: 通过 props 添加功能
2. **组合组件**: 组合多个小组件
3. **创建新组件**: 参考本文档规范

### Q: 如何确保响应式？

A: 使用 CSS Grid + Flexbox，避免固定宽度：

```tsx
// ✅ 好
<div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>

// ❌ 差
<div style={{ display: 'grid', gridTemplateColumns: '292px 1fr' }}>
```

---

*本文档与代码同步更新，如有不一致请以实际代码为准。*
