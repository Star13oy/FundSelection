# 变更记录

## 2026-03-31

### 前端交互与展示

- 修复 `详情` 按钮跳转后接口报错的问题，详情页重新走稳定的 `FundDetail` 组装逻辑。
- `选基` 页面接入真实分页，支持上一页、下一页、总数与页大小联动。
- `选基` 页面补齐基金规模展示，类型列改为更易读的“类别 + 规模”结构。
- 首页推荐表格与选基表格统一了 A 股视觉规则：
  - 收益为红色
  - 亏损为绿色
  - 回撤按同一套红绿规则展示
  - 平盘值使用中性色
- 优化首页表头与筛选表头的排版，减少生硬换行和拥挤感。

### 后端接口与数据

- `/api/v1/funds` 列表接口补充以下字段：
  - `fund_type`
  - `scale_billion`
  - `one_year_return`
  - `max_drawdown`
- `/api/v1/funds/{code}` 详情接口修复重复字段传参导致的 `500` 问题。
- 新增 `/api/v1/market/sector-heat`，使用板块代表 ETF 生成实时热度卡片数据。
- 市场行情刷新改为后台异步执行，同时提供刷新状态查询，降低页面阻塞感。
- 风险偏好切换增加缓存，减少重复计算综合评分带来的延迟。

### 实时数据来源

- 板块热度当前使用代表性 ETF 映射：
  - 半导体：`512480`
  - 白酒：`512690`
  - 新能源：`516160`
  - 人工智能：`159819`
- 行情刷新完成后会主动清空板块热度缓存，确保下次读取尽量使用新数据。

### 本地运行约定

- 前端开发端口固定为 `http://127.0.0.1:5173`
- 后端开发端口固定为 `http://127.0.0.1:8000`
- 本地数据库按当前项目约定使用 MySQL，默认连接信息为 `root/root`

### 本轮涉及的主要文件

- `backend/app/main.py`
- `backend/app/models.py`
- `backend/app/store.py`
- `backend/database/schema_mysql.sql`
- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- `frontend/src/types.ts`
- `frontend/src/pages/HomePage.tsx`
- `frontend/src/pages/PickerPage.tsx`
- `frontend/src/components/dashboard/RecommendationTable.tsx`
- `frontend/src/components/dashboard/RiskInsight.tsx`
- `frontend/vite.config.ts`
