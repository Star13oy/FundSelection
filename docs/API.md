# API 文档

目标受众：前端开发人员和API用户

## 1. 概览

### 基本信息

- **基础URL**：`http://localhost:8000/api/v1`
- **认证方式**：当前不需要认证（未来版本将添加JWT认证）
- **响应格式**：JSON
- **CORS支持**：已配置支持前端开发服务器

### 通用响应格式

所有API响应都遵循以下格式：

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2024-03-30T10:00:00Z"
}
```

错误响应格式：

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Fund not found",
    "details": "Fund code '000001' does not exist"
  },
  "timestamp": "2024-03-30T10:00:00Z"
}
```

## 2. 端点文档

### 2.1 基金相关接口

#### GET /api/v1/funds

获取基金列表，支持多种筛选和排序选项。

**请求参数**：

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `channel` | string | 否 | - | 交易渠道：场内、场外 |
| `category` | string | 否 | - | 基金类别：股票型、混合型、债券型等 |
| `risk_level` | string | 否 | - | 风险等级：低、中低、中、中高、高 |
| `min_years` | number | 否 | - | 最小运作年限 |
| `min_scale` | number | 否 | - | 最小规模（亿元） |
| `max_scale` | number | 否 | - | 最大规模（亿元） |
| `max_fee` | number | 否 | - | 最大费率（%） |
| `keyword` | string | 否 | - | 关键字搜索（基金名称或代码） |
| `risk_profile` | string | 否 | "均衡" | 风险偏好：保守、均衡、进取 |
| `sort_by` | string | 否 | "final_score" | 排序字段 |
| `sort_order` | string | 否 | "desc" | 排序方向 |
| `page` | number | 否 | 1 | 页码 |
| `page_size` | number | 否 | 20 | 每页数量（最大100） |

**响应示例**：

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "code": "110011",
        "name": "易方达蓝筹精选混合",
        "channel": "场外",
        "category": "混合型",
        "risk_level": "中",
        "liquidity_label": "高流动性",
        "final_score": 85.5,
        "base_score": 82.3,
        "policy_score": 88.7,
        "overlay_weight": 0.1,
        "market": {
          "current_price": 1.2345,
          "price_change_pct": 0.5,
          "nav": 1.2345,
          "nav_date": "2024-03-30"
        },
        "updated_at": "2024-03-30T10:00:00Z"
      }
    ],
    "total": 156,
    "page": 1,
    "page_size": 20
  },
  "timestamp": "2024-03-30T10:00:00Z"
}
```

**状态码**：
- 200：成功
- 400：参数错误
- 500：服务器错误

**示例请求**：

```bash
# 获取股票型基金
curl "http://localhost:8000/api/v1/funds?category=股票型&page=1&page_size=10"

# 获取中等风险偏好的基金
curl "http://localhost:8000/api/v1/funds?risk_level=中&risk_profile=均衡"

# 搜索包含"蓝筹"的基金
curl "http://localhost:8000/api/v1/funds?keyword=蓝筹&sort_by=final_score&sort_order=desc"
```

#### GET /api/v1/funds/{code}

获取特定基金的详细信息。

**路径参数**：
- `code`：基金代码（必填）

**查询参数**：
- `risk_profile`：风险偏好（可选，默认"均衡"）

**响应示例**：

```json
{
  "success": true,
  "data": {
    "code": "110011",
    "name": "易方达蓝筹精选混合",
    "channel": "场外",
    "category": "混合型",
    "risk_level": "中",
    "liquidity_label": "高流动性",
    "final_score": 85.5,
    "base_score": 82.3,
    "policy_score": 88.7,
    "overlay_weight": 0.1,
    "explanation": {
      "plus": [
        "长期业绩优异",
        "风险控制良好",
        "成本效率较高"
      ],
      "minus": [
        "近期波动较大",
        "管理费率偏高"
      ],
      "risk_tip": "适合风险承受能力中等的投资者",
      "applicable": "适合追求长期稳健收益的投资者",
      "disclaimer": "基金投资有风险，过往业绩不代表未来表现",
      "formula": "最终评分 = 基础评分 × (1 - 权重) + 政策评分 × 权重"
    },
    "years": 8.5,
    "scale_billion": 456.78,
    "one_year_return": 12.5,
    "max_drawdown": -8.3,
    "fee": 1.5,
    "tracking_error": 2.1,
    "updated_at": "2024-03-30T10:00:00Z",
    "factors": {
      "returns": 88.2,
      "risk_control": 82.5,
      "risk_adjusted": 85.1,
      "stability": 78.9,
      "cost_efficiency": 76.3,
      "liquidity": 95.6,
      "survival_quality": 90.2
    },
    "policy": {
      "support": 85.0,
      "execution": 92.3,
      "regulation_safety": 88.7
    },
    "market": {
      "current_price": 1.2345,
      "previous_close": 1.2289,
      "intraday_high": 1.2389,
      "intraday_low": 1.2256,
      "open_price": 1.2298,
      "price_change_pct": 0.46,
      "price_change_value": 0.0056,
      "nav": 1.2345,
      "nav_date": "2024-03-30",
      "nav_estimate": 1.2356,
      "nav_estimate_change_pct": 0.08
    }
  },
  "timestamp": "2024-03-30T10:00:00Z"
}
```

**状态码**：
- 200：成功
- 404：基金未找到
- 500：服务器错误

**示例请求**：

```bash
curl "http://localhost:8000/api/v1/funds/110011?risk_profile=保守"
```

#### POST /api/v1/funds/refresh

刷新因子计算和市场数据。

**请求体**：空

**响应示例**：

```json
{
  "success": true,
  "data": {
    "funds_refreshed": 156,
    "market_data_updated": 89,
    "factor_calculations": 156,
    "benchmark_data_synced": 12,
    "execution_time_seconds": 45.2
  },
  "message": "基金数据刷新完成",
  "timestamp": "2024-03-30T10:00:00Z"
}
```

**状态码**：
- 200：成功
- 500：服务器错误

**示例请求**：

```bash
curl -X POST "http://localhost:8000/api/v1/funds/refresh"
```

### 2.2 市场数据接口

#### GET /api/v1/market/quotes

获取实时市场行情数据。

**响应示例**：

```json
{
  "success": true,
  "data": {
    "quotes": [
      {
        "code": "110011",
        "name": "易方达蓝筹精选混合",
        "current_price": 1.2345,
        "previous_close": 1.2289,
        "price_change_pct": 0.46,
        "price_change_value": 0.0056,
        "volume": 1256000,
        "turnover": 1550000,
        "timestamp": "2024-03-30T15:00:00Z"
      }
    ],
    "last_updated": "2024-03-30T15:00:00Z"
  },
  "timestamp": "2024-03-30T10:00:00Z"
}
```

**状态码**：
- 200：成功
- 500：服务器错误

**示例请求**：

```bash
curl "http://localhost:8000/api/v1/market/quotes"
```

#### POST /api/v1/market/refresh

刷新市场数据（从akshare获取最新数据）。

**请求体**：空

**响应示例**：

```json
{
  "success": true,
  "data": {
    "quotes_updated": 89,
    "nav_data_updated": 156,
    "new_funds_detected": 2,
    "execution_time_seconds": 23.5,
    "next_update_at": "2024-03-30T15:30:00Z"
  },
  "message": "市场数据刷新完成",
  "timestamp": "2024-03-30T10:00:00Z"
}
```

**状态码**：
- 200：成功
- 500：服务器错误

**示例请求**：

```bash
curl -X POST "http://localhost:8000/api/v1/market/refresh"
```

### 2.3 自选列表接口

#### GET /api/v1/watchlist

获取用户自选列表。

**查询参数**：
- `risk_profile`：风险偏好（可选，默认"均衡"）

**响应示例**：

```json
{
  "success": true,
  "data": [
    {
      "code": "110011",
      "name": "易方达蓝筹精选混合",
      "channel": "场外",
      "category": "混合型",
      "risk_level": "中",
      "liquidity_label": "高流动性",
      "final_score": 85.5,
      "base_score": 82.3,
      "policy_score": 88.7,
      "overlay_weight": 0.1,
      "alerts": [
        {
          "type": "price_alert",
          "message": "基金价格上涨超过5%",
          "severity": "warning",
          "timestamp": "2024-03-30T10:00:00Z"
        }
      ],
      "market": {
        "current_price": 1.2345,
        "price_change_pct": 0.5
      }
    }
  ],
  "timestamp": "2024-03-30T10:00:00Z"
}
```

**状态码**：
- 200：成功
- 500：服务器错误

**示例请求**：

```bash
curl "http://localhost:8000/api/v1/watchlist?risk_profile=进取"
```

#### POST /api/v1/watchlist

添加基金到自选列表。

**请求体**：

```json
{
  "code": "110011"
}
```

**响应示例**：

```json
{
  "success": true,
  "data": {
    "status": "ok",
    "code": "110011",
    "message": "基金已添加到自选列表"
  },
  "timestamp": "2024-03-30T10:00:00Z"
}
```

**状态码**：
- 200：成功
- 400：请求参数错误
- 404：基金未找到
- 409：基金已在自选列表中
- 500：服务器错误

**示例请求**：

```bash
curl -X POST "http://localhost:8000/api/v1/watchlist" \
  -H "Content-Type: application/json" \
  -d '{"code": "110011"}'
```

#### DELETE /api/v1/watchlist/{code}

从自选列表移除基金。

**路径参数**：
- `code`：基金代码

**响应示例**：

```json
{
  "success": true,
  "data": {
    "status": "ok",
    "code": "110011",
    "message": "基金已从自选列表移除"
  },
  "timestamp": "2024-03-30T10:00:00Z"
}
```

**状态码**：
- 200：成功
- 404：基金不在自选列表中
- 500：服务器错误

**示例请求**：

```bash
curl -X DELETE "http://localhost:8000/api/v1/watchlist/110011"
```

### 2.4 基金对比接口

#### GET /api/v1/compare

对比多个基金的评分和指标。

**查询参数**：
- `codes`：基金代码列表（必填，2-5个）
- `risk_profile`：风险偏好（可选，默认"均衡"）

**响应示例**：

```json
[
  {
    "code": "110011",
    "name": "易方达蓝筹精选混合",
    "channel": "场外",
    "category": "混合型",
    "risk_level": "中",
    "liquidity_label": "高流动性",
    "final_score": 85.5,
    "base_score": 82.3,
    "policy_score": 88.7,
    "overlay_weight": 0.1,
    "market": {
      "current_price": 1.2345,
      "price_change_pct": 0.5
    }
  }
]
```

**状态码**：
- 200：成功
- 400：参数错误
- 500：服务器错误

**示例请求**：

```bash
curl "http://localhost:8000/api/v1/compare?codes=110011,210008,110022"
```

### 2.5 数据同步接口

#### POST /api/v1/funds/sync

同步基金数据（从数据源获取最新基金列表）。

**请求体**：空

**响应示例**：

```json
{
  "success": true,
  "data": {
    "total_funds": 156,
    "new_funds": 2,
    "updated_funds": 5,
    "deleted_funds": 0,
    "execution_time_seconds": 15.3,
    "last_sync": "2024-03-30T10:00:00Z"
  },
  "message": "基金数据同步完成",
  "timestamp": "2024-03-30T10:00:00Z"
}
```

**状态码**：
- 200：成功
- 500：服务器错误

**示例请求**：

```bash
curl -X POST "http://localhost:8000/api/v1/funds/sync"
```

### 2.6 政策验证接口

#### POST /api/v1/policy/validate-timestamps

验证政策时间戳的有效性。

**请求体**：

```json
{
  "policy_id": "POLICY_001",
  "published_at": "2024-03-30T09:00:00Z",
  "effective_from": "2024-03-30T10:00:00Z",
  "observed_at": "2024-03-30T11:00:00Z"
}
```

**响应示例**：

```json
{
  "success": true,
  "data": {
    "policy_id": "POLICY_001",
    "valid": true,
    "errors": []
  },
  "timestamp": "2024-03-30T10:00:00Z"
}
```

**状态码**：
- 200：成功
- 400：参数错误
- 500：服务器错误

**示例请求**：

```bash
curl -X POST "http://localhost:8000/api/v1/policy/validate-timestamps" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_id": "POLICY_001",
    "published_at": "2024-03-30T09:00:00Z",
    "effective_from": "2024-03-30T10:00:00Z",
    "observed_at": "2024-03-30T11:00:00Z"
  }'
```

## 3. 数据模型

### 3.1 基金数据模型

#### Fund
```typescript
interface Fund {
  code: string;           // 基金代码
  name: string;          // 基金名称
  channel: "场内" | "场外"; // 交易渠道
  category: string;       // 基金类别
  risk_level: string;     // 风险等级
  liquidity_label: string;// 流动性标签
  years: number;          // 运作年限
  scale_billion: number;  // 规模（亿元）
  one_year_return: number;// 近一年收益率
  max_drawdown: number;   // 最大回撤
  fee: number;           // 管理费率
  tracking_error: number; // 跟踪误差
  updated_at: string;     // 更新时间
  factors: FactorMetrics; // 因子指标
  policy: PolicyMetrics;  // 政策指标
}
```

#### FundScore
```typescript
interface FundScore {
  code: string;           // 基金代码
  name: string;          // 基金名称
  channel: string;       // 交易渠道
  category: string;       // 基金类别
  risk_level: string;     // 风险等级
  liquidity_label: string;// 流动性标签
  final_score: number;    // 最终评分
  base_score: number;     // 基础评分
  policy_score: number;   // 政策评分
  overlay_weight: number; // 权重
  explanation: Explanation; // 解释说明
  market?: MarketSnapshot; // 市场数据
}
```

#### FactorMetrics
```typescript
interface FactorMetrics {
  returns: number;               // 收益率因子
  risk_control: number;           // 风险控制因子
  risk_adjusted: number;         // 风险调整收益因子
  stability: number;              // 稳定性因子
  cost_efficiency: number;       // 成本效率因子
  liquidity: number;             // 流动性因子
  survival_quality: number;      // 存续质量因子
}
```

#### PolicyMetrics
```typescript
interface PolicyMetrics {
  support: number;        // 政策支持度
  execution: number;      // 政策执行度
  regulation_safety: number; // 监管安全度
}
```

#### Explanation
```typescript
interface Explanation {
  plus: string[];         // 优势说明
  minus: string[];        // 劣势说明
  risk_tip: string;       // 风险提示
  applicable: string;     // 适用人群
  disclaimer: string;      // 免责声明
  formula: string;        // 评分公式
}
```

### 3.2 市场数据模型

#### MarketSnapshot
```typescript
interface MarketSnapshot {
  current_price?: number;         // 当前价格
  previous_close?: number;       // 前收盘价
  intraday_high?: number;        // 日内最高价
  intraday_low?: number;         // 日内最低价
  open_price?: number;           // 开盘价
  price_change_pct?: number;     // 价格涨跌幅
  price_change_value?: number;   // 价格涨跌值
  nav?: number;                  // 净值
  nav_date?: string;             // 净值日期
  nav_estimate?: number;        // 净值估算
  nav_estimate_change_pct?: number; // 净值估算涨跌幅
}
```

### 3.3 自选列表模型

#### WatchlistItem
```typescript
interface WatchlistItem {
  code: string; // 基金代码
}
```

#### WatchlistScore
```typescript
interface WatchlistScore extends FundScore {
  alerts: Alert[]; // 警告信息
}
```

#### Alert
```typescript
interface Alert {
  type: string;        // 警告类型
  message: string;      // 警告消息
  severity: string;    // 严重程度
  timestamp: string;    // 时间戳
}
```

### 3.4 对比数据模型

#### ComparisonResult
```typescript
interface ComparisonResult {
  funds: FundScore[];  // 基金评分列表
  summary: {
    best_performer: string;     // 最佳表现者
    highest_risk: string;       // 最高风险
    lowest_fee: string;          // 最低费率
    recommendation: string;     // 推荐建议
  };
}
```

## 4. 错误处理

### 4.1 错误代码

| 错误代码 | HTTP状态码 | 描述 |
|----------|------------|------|
| `NOT_FOUND` | 404 | 资源未找到 |
| `INVALID_PARAMETER` | 400 | 请求参数无效 |
| `DUPLICATE_RESOURCE` | 409 | 资源已存在 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |
| `RATE_LIMITED` | 429 | 请求频率受限 |
| `AUTH_REQUIRED` | 401 | 需要认证 |
| `FORBIDDEN` | 403 | 访问被拒绝 |

### 4.2 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Fund not found",
    "details": "Fund code '000001' does not exist",
    "request_id": "req_1234567890",
    "timestamp": "2024-03-30T10:00:00Z"
  }
}
```

### 4.3 常见错误示例

#### 基金未找到
```bash
curl "http://localhost:8000/api/v1/funds/000001"
```

响应：
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Fund not found",
    "details": "Fund code '000001' does not exist"
  },
  "timestamp": "2024-03-30T10:00:00Z"
}
```

#### 参数验证失败
```bash
curl "http://localhost:8000/api/v1/funds?page=0"
```

响应：
```json
{
  "success": false,
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid page parameter",
    "details": "Page must be greater than 0"
  },
  "timestamp": "2024-03-30T10:00:00Z"
}
```

## 5. 限流和认证

### 5.1 当前状态

- **认证**：未实现（所有接口公开访问）
- **限流**：未实现（无频率限制）
- **CORS**：已配置支持开发环境

### 5.2 未来计划

- **JWT认证**：为生产环境实现JWT令牌认证
- **API密钥**：为第三方集成实现API密钥认证
- **限流策略**：实现基于用户/IP的限流
- **权限控制**：基于角色的访问控制（RBAC）

## 6. 测试和调试

### 6.1 API测试工具

推荐使用以下工具进行API测试：

- **Postman**：图形化API测试工具
- **curl**：命令行测试工具
- **Insomnia**：现代API测试工具
- **Swagger UI**：交互式API文档（未来实现）

### 6.2 测试示例

```bash
# 测试基金列表接口
curl "http://localhost:8000/api/v1/funds?category=股票型&page=1&page_size=5" -H "Accept: application/json"

# 测试基金详情接口
curl "http://localhost:8000/api/v1/funds/110011" -H "Accept: application/json"

# 测试自选列表添加
curl -X POST "http://localhost:8000/api/v1/watchlist" \
  -H "Content-Type: application/json" \
  -d '{"code": "110011"}'

# 测试自选列表获取
curl "http://localhost:8000/api/v1/watchlist"
```

### 6.3 监控和日志

- 应用日志：`logs/app.log`
- API访问日志：服务器访问日志
- 性能监控：响应时间、错误率等指标
- 错误追踪：集成Sentry（未来实现）

## 7. 版本和更新

### 7.1 版本控制

- **当前版本**：v1.0.0
- **API版本**：/api/v1/
- **向后兼容**：保持向后兼容性
- **更新通知**：通过API响应头中的版本号标识

### 7.2 更新日志

#### v1.0.0 (2024-03-30)
- 初始版本发布
- 实现所有核心API端点
- 支持基金筛选、查询、自选列表功能
- 实现市场数据获取和刷新功能

## 8. 示例代码

### 8.1 JavaScript/TypeScript

```typescript
// 基金API客户端
class FundApiClient {
  private baseUrl = 'http://localhost:8000/api/v1';

  async getFunds(params: FundSearchParams) {
    const response = await fetch(`${this.baseUrl}/funds?${new URLSearchParams(params)}`);
    return response.json();
  }

  async getFund(code: string, riskProfile: string = '均衡') {
    const response = await fetch(`${this.baseUrl}/funds/${code}?risk_profile=${riskProfile}`);
    return response.json();
  }

  async addToWatchlist(code: string) {
    const response = await fetch(`${this.baseUrl}/watchlist`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code })
    });
    return response.json();
  }
}

// 使用示例
const client = new FundApiClient();
const funds = await client.getFunds({ category: '股票型', page: 1, page_size: 10 });
console.log(funds);
```

### 8.2 Python

```python
import requests

class FundAPIClient:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url

    def get_funds(self, **params):
        response = requests.get(f"{self.base_url}/funds", params=params)
        response.raise_for_status()
        return response.json()

    def get_fund(self, code, risk_profile="均衡"):
        response = requests.get(f"{self.base_url}/funds/{code}",
                              params={"risk_profile": risk_profile})
        response.raise_for_status()
        return response.json()

    def add_to_watchlist(self, code):
        response = requests.post(f"{self.base_url}/watchlist",
                               json={"code": code})
        response.raise_for_status()
        return response.json()

# 使用示例
client = FundAPIClient()
funds = client.get_funds(category="股票型", page=1, page_size=10)
print(funds)
```

## 9. 支持和反馈

### 9.1 技术支持

如果遇到API相关问题，请：

1. **检查错误日志**：查看 `logs/app.log` 文件
2. **验证网络连接**：确保API服务器正常运行
3. **检查参数格式**：确保所有请求参数格式正确
4. **查看最新文档**：访问 [docs/API.md](docs/API.md)

### 9.2 问题报告

报告问题时，请提供以下信息：

- API端点和请求方法
- 请求参数和请求体
- 完整的错误响应
- 环境信息（服务器版本、依赖版本等）
- 复现步骤

### 9.3 功能建议

欢迎提交API功能改进建议：

- GitHub Issues：[https://github.com/Star13oy/FundSelection/issues](https://github.com/Star13oy/FundSelection/issues)
- 邮箱：your-email@example.com

## 10. 相关资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [HTTP 状态码](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [JSON API 规范](https://jsonapi.org/)
- [REST API 设计指南](https://restfulapi.net/)