# 测试策略（MVP）

## 1. 目标
- 单元测试覆盖率 >= 90%（前后端分别统计）
- 集成测试 100% 通过
- 关键业务链路可重复验证

## 2. 测试分层

### 2.1 后端单元测试
范围：
- 评分函数
- 权重选择逻辑
- 推荐解释生成逻辑
- 参数校验

工具：pytest + pytest-cov
门槛：`--cov-fail-under=90`

### 2.2 前端单元测试
范围：
- 评分展示与解释渲染函数
- 页面切换与核心交互
- API 调用封装

工具：Vitest + Testing Library
门槛：`coverage.thresholds.lines = 90`、`coverage.thresholds.statements = 90`、`coverage.thresholds.functions = 80`、`coverage.thresholds.branches = 80`

执行命令：
- `cd /home/jerry/projects/fund-quant-web-docs/frontend && npm run check`
- `cd /home/jerry/projects/fund-quant-web-docs/frontend && npm run test:coverage`

### 2.3 集成测试
范围：
1. 筛选 -> 评分 -> 推荐列表
2. 详情 -> 解释输出
3. 对比（2~5 只）
4. 观察池增删查
5. 风险偏好切换影响结果

工具：pytest（FastAPI TestClient）
门槛：全量通过（100%）

## 3. CI 门禁
必须同时通过：
1. backend lint/type-check/unit
2. frontend lint/type-check/unit
3. integration tests

任何一项失败都禁止合并。
