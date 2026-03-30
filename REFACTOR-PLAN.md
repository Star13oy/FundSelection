# 基金量化选基助手 - 完整重构计划

> 计划版本：v1.0
> 制定日期：2026-03-30
> 计划负责人：Claude (OMC Planning Agent)
> 预计周期：6-8周

---

## 📊 执行摘要

### 项目现状
- **前端完成度**：85%（已重构，基于 Figma 设计）
- **后端完成度**：35%（有框架，但核心逻辑缺失）
- **整体健康度**：⚠️ 严重问题

### 🚨 关键问题
1. **所有因子评分都是伪造的**（使用 MD5 哈希伪随机生成）
2. **没有历史数据存储**（无法计算真实因子）
3. **政策数据完全缺失**
4. **数据库缺少索引**（性能瓶颈）

### 🎯 重构目标
1. **实现真实因子计算引擎**
2. **建立历史数据存储和计算能力**
3. **支持 SQLite 便于迁移**
4. **完善政策数据系统**
5. **优化性能和可维护性**

---

## 🗺️ 技术架构设计

### 数据流架构

```
┌─────────────────────────────────────────────────────────────┐
│                        数据获取层                            │
├─────────────────────────────────────────────────────────────┤
│  akshare (基金列表)  akshare (历史净值)  政策事件 (手动维护)   │
└─────────────┬───────────────────────┬───────────────────────┘
              │                       │
              ▼                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据处理层                              │
├─────────────────────────────────────────────────────────────┤
│  历史数据存储 → 因子计算引擎 → 标准化处理 → 评分系统     │
│  (SQLite/MySQL)    (pandas)      (winsorize)   (权重)      │
└─────────────┬───────────────────────┴───────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                              │
├─────────────────────────────────────────────────────────────┤
│  SQLite (开发)  │  MySQL (生产)  │  Redis (缓存)          │
│  - 零配置      │  - 连接池      │  - 1分钟 TTL           │
│  - 便于迁移    │  - 读写分离    │  - 快速查询            │
└─────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API 服务层                               │
├─────────────────────────────────────────────────────────────┤
│  FastAPI → 数据验证 → 业务逻辑 → 响应返回                      │
└─────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                      前端展示层                               │
├─────────────────────────────────────────────────────────────┤
│  React + TypeScript → 组件化 UI → 图表展示                  │
└─────────────────────────────────────────────────────────────┘
```

### 数据库架构

#### 开发环境（SQLite）
```
fund_selection.db
├── funds                 # 基金基础信息
├── fund_nav_history      # 历史净值数据（新增）
├── market_quotes         # 实时行情
├── market_quotes_history # 历史行情（新增）
├── policy_events         # 政策事件（新增）
├── watchlist             # 观察池
└── data_change_log       # 变更日志（新增）
```

#### 生产环境（MySQL）
```
fund_selection
├── funds                 # 基金基础信息
├── fund_nav_history      # 历史净值数据
├── market_quotes         # 实时行情
├── market_quotes_history # 历史行情
├── policy_events         # 政策事件
├── watchlist             # 观察池
└── data_change_log       # 变更日志
```

---

## 📋 分阶段实施计划

### Phase 1: 数据层重构（Week 1-2）

#### 目标
- 实现数据库抽象层，支持 SQLite/MySQL 切换
- 添加历史数据表
- 优化数据库索引
- 实现数据迁移脚本

#### 任务清单

**1.1 数据库适配器层**
- [ ] 创建 `database_adapter.py`
- [ ] 实现 `DatabaseAdapter` 接口
- [ ] 实现 `SQLiteAdapter`
- [ ] 实现 `MySQLAdapter`
- [ ] 创建工厂函数 `create_adapter()`
- [ ] 编写单元测试

**1.2 数据库 Schema 更新**
- [ ] 创建 `schema_sqlite.sql`
- [ ] 创建 `schema_mysql.sql`
- [ ] 添加 `fund_nav_history` 表
- [ ] 添加 `market_quotes_history` 表
- [ ] 添加 `policy_events` 表
- [ ] 添加 `data_change_log` 表
- [ ] 添加所有必要的索引

**1.3 数据迁移工具**
- [ ] 修改 `db.py` 使用适配器
- [ ] 修改 `store.py` 使用适配器
- [ ] 替换 `ON DUPLICATE KEY UPDATE` 为 `ON CONFLICT`
- [ ] 替换 `INSERT IGNORE` 为 `INSERT OR IGNORE`
- [ ] 编写数据迁移脚本
- [ ] 测试 MySQL → SQLite 迁移

**1.4 连接池优化**
- [ ] 实现数据库连接池
- [ ] 配置连接参数
- [ ] 添加连接健康检查

**验收标准**
- ✅ 可以通过环境变量切换 SQLite/MySQL
- ✅ 所有测试通过
- ✅ 迁移脚本执行成功
- ✅ 查询性能提升 50%+

---

### Phase 2: 因子计算引擎（Week 3-4）

#### 目标
- 实现真实的因子计算逻辑
- 从 akshare 获取历史净值数据
- 计算所有 7 大类因子
- 实现因子标准化和异常值处理

#### 任务清单

**2.1 历史数据获取**
- [ ] 扩展 `universe.py` 获取历史净值
- [ ] 实现 `fetch_fund_nav_history()` 函数
- [ ] 支持增量更新历史数据
- [ ] 处理缺失数据和异常值
- [ ] 存储到 `fund_nav_history` 表

**2.2 因子计算函数**
- [ ] 创建 `factors/calculator.py`
- [ ] 实现收益率计算（6月、1年、3年）
  - [ ] `calculate_annual_return()`
  - [ ] `calculate_cumulative_return()`
- [ ] 实现风险指标计算
  - [ ] `calculate_max_drawdown()`
  - [ ] `calculate_volatility()`
  - [ ] `calculate_downside_deviation()`
- [ ] 实现风险调整收益指标
  - [ ] `calculate_sharpe_ratio()`
  - [ ] `calculate_sortino_ratio()`
- [ ] 实现稳定性指标
  - [ ] `calculate_rolling_win_rate()`
  - [ ] `calculate_drawdown_recovery()`
- [ ] 实现成本效率指标
  - [ ] `calculate_expense_ratio()`
  - [ ] `calculate_tracking_error()`

**2.3 因子标准化**
- [ ] 创建 `factors/standardizer.py`
- [ ] 实现 `winsorize()` 异常值处理
- [ ] 实现 `standardize_by_category()` 按类别标准化
- [ ] 实现 `handle_missing_values()` 缺失值处理
- [ ] 编写单元测试验证计算正确性

**2.4 因子计算集成**
- [ ] 修改 `universe.py` 调用真实计算函数
- [ ] 移除伪随机生成逻辑
- [ ] 实现计算结果缓存
- [ ] 添加计算进度日志

**验收标准**
- ✅ 所有因子都是真实计算
- ✅ 与 akshare 数据对比验证
- ✅ 计算性能 < 5秒/基金
- ✅ 单元测试覆盖率 > 90%

---

### Phase 3: 政策数据系统（Week 5）

#### 目标
- 建立政策事件数据库
- 实现行业-政策映射
- 计算政策因子分数
- 集成到评分系统

#### 任务清单

**3.1 政策事件数据库**
- [ ] 创建 `policy_events` 表
- [ ] 设计政策事件数据模型
- [ ] 实现政策事件 CRUD 接口
- [ ] 添加政策事件管理界面（可选）

**3.2 行业-政策映射**
- [ ] 创建 `sector_policy_mapping.py`
- [ ] 定义行业分类（宽基、行业主题等）
- [ ] 实现政策-行业关联逻辑
- [ ] 支持手动配置映射关系

**3.3 政策分数计算**
- [ ] 创建 `policy/scoring.py`
- [ ] 实现政策强度评分（0-100）
- [ ] 实现执行进度评分（0-100）
- [ ] 实现监管安全度评分（0-100）
- [ ] 实现 `calculate_policy_score()` 综合评分

**3.4 政策数据集成**
- [ ] 修改 `universe.py` 调用政策评分
- [ ] 移除伪随机政策评分
- [ ] 实现政策数据更新机制
- [ ] 添加政策事件时间戳验证

**3.5 初始政策数据**
- [ ] 手动录入 20-50 个典型政策事件
- [ ] 覆盖主要行业（科技、医药、消费、新能源等）
- [ ] 设置合理的默认评分
- [ ] 编写政策数据维护文档

**验收标准**
- ✅ 政策事件表有真实数据
- ✅ 政策分数基于真实事件计算
- ✅ 支持 CRUD 操作
- ✅ 与评分系统正常集成

---

### Phase 4: 性能优化（Week 6）

#### 目标
- 实现多层缓存
- 优化数据库查询
- 实现异步更新
- 添加监控和日志

#### 任务清单

**4.1 Redis 缓存层**
- [ ] 集成 Redis（可选）
- [ ] 实现缓存装饰器
- [ ] 配置缓存策略
  - 基金列表：5分钟 TTL
  - 基金详情：10分钟 TTL
  - 市场行情：1分钟 TTL
- [ ] 实现缓存失效机制
- [ ] 添加缓存预热

**4.2 数据库优化**
- [ ] 添加所有必要索引
- [ ] 优化慢查询
- [ ] 实现数据库连接池
- [ ] 配置查询超时
- [ ] 添加慢查询日志

**4.3 异步数据更新**
- [ ] 实现后台任务调度
- [ ] 支持增量更新行情
- [ ] 实现失败重试机制
- [ ] 添加更新进度通知
- [ ] 配置更新频率策略

**4.4 监控和日志**
- [ ] 集成 Python logging
- [ ] 实现结构化日志
- [ ] 添加性能监控
  - [ ] 数据更新耗时
  - [ ] 因子计算耗时
  - [ ] API 响应时间
- [ ] 添加错误告警
- [ ] 实现健康检查接口

**验收标准**
- ✅ API 响应时间 < 500ms（P95）
- ✅ 数据更新不阻塞 API
- ✅ 缓存命中率 > 80%
- ✅ 错误有完整日志

---

### Phase 5: 测试与文档（Week 7-8）

#### 目标
- 完善测试覆盖
- 编写开发文档
- 准备部署指南
- 性能测试

#### 任务清单

**5.1 测试完善**
- [ ] 补充因子计算单元测试
- [ ] 添加数据库迁移测试
- [ ] 添加集成测试
- [ ] 添加端到端测试
- [ ] 性能测试
  - [ ] 并发用户测试
  - [ ] 大数据量测试
  - [ ] 长时间运行测试

**5.2 文档完善**
- [ ] 更新 README.md
- [ ] 编写 SETUP.md（安装指南）
- [ ] 编写 MIGRATION.md（数据库迁移指南）
- [ ] 编写 API.md（API 文档）
- [ ] 编写 DEPLOYMENT.md（部署指南）
- [ ] 更新架构设计文档

**5.3 部署准备**
- [ ] 编写 Docker 配置
- [ ] 编写 docker-compose.yml
- [ ] 配置环境变量
- [ ] 准备部署脚本
- [ ] 编写运维文档

**验收标准**
- ✅ 测试覆盖率 > 80%
- ✅ 文档完整且清晰
- ✅ 可以一键部署
- ✅ 性能满足预期

---

## 🎯 核心技术方案

### 1. 数据库抽象层

```python
# database_adapter.py
from abc import ABC, abstractmethod

class DatabaseAdapter(ABC):
    @abstractmethod
    def connect(self): pass

    @abstractmethod
    def execute(self, sql: str, params: tuple = None): pass

    @abstractmethod
    def insert_on_duplicate(self, table: str, data: dict, conflict_key: str): pass

class SQLiteAdapter(DatabaseAdapter):
    def __init__(self, db_path: str = "fund_selection.db"):
        self.db_path = db_path

    def connect(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def insert_on_duplicate(self, table: str, data: dict, conflict_key: str):
        # SQLite: INSERT OR REPLACE
        fields = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        sql = f"INSERT OR REPLACE INTO {table} ({fields}) VALUES ({placeholders})"
        return self.execute(sql, tuple(data.values()))

class MySQLAdapter(DatabaseAdapter):
    def insert_on_duplicate(self, table: str, data: dict, conflict_key: str):
        # MySQL: ON DUPLICATE KEY UPDATE
        fields = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        updates = ', '.join([f"{k}=VALUES({k})" for k in data.keys()])
        sql = f"""
            INSERT INTO {table} ({fields})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {updates}
        """
        return self.execute(sql, tuple(data.values()))

# 工厂函数
def create_adapter() -> DatabaseAdapter:
    db_type = os.getenv("DB_TYPE", "sqlite")
    if db_type == "sqlite":
        return SQLiteAdapter(os.getenv("SQLITE_DB_PATH", "fund_selection.db"))
    else:
        return MySQLAdapter({...})
```

### 2. 因子计算引擎

```python
# factors/calculator.py
import pandas as pd
from typing import List

class FactorCalculator:
    def __init__(self, nav_history: pd.DataFrame):
        """
        nav_history: DataFrame with columns
        - fund_code: str
        - date: datetime
        - unit_nav: float
        - accumulated_nav: float (optional)
        """
        self.nav_history = nav_history

    def calculate_annual_return(self, fund_code: str, years: List[int] = [1]) -> dict:
        """计算年化收益率"""
        fund_data = self.nav_history[
            self.nav_history['fund_code'] == fund_code
        ].sort_values('date')

        results = {}
        for year in years:
            # 获取 year 年前的数据
            start_date = fund_data['date'].min() + pd.DateOffset(years=year)
            period_data = fund_data[fund_data['date'] >= start_date]

            if len(period_data) < 2:
                results[f"{year}y_return"] = None
                continue

            # 计算年化收益率
            first_nav = period_data['unit_nav'].iloc[0]
            last_nav = period_data['unit_nav'].iloc[-1]
            annual_return = (last_nav / first_nav) ** (252 / len(period_data)) - 1
            results[f"{year}y_return"] = annual_return

        return results

    def calculate_max_drawdown(self, fund_code: str) -> float:
        """计算最大回撤"""
        fund_data = self.nav_history[
            self.nav_history['fund_code'] == fund_code
        ].sort_values('date')

        if len(fund_data) < 2:
            return 0.0

        cumulative = fund_data['unit_nav'].values
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        return float(max_drawdown) if not np.isnan(max_drawdown) else 0.0

    def calculate_volatility(self, fund_code: str, period: int = 252) -> float:
        """计算年化波动率"""
        fund_data = self.nav_history[
            self.nav_history['fund_code'] == fund_code
        ].sort_values('date')

        if len(fund_data) < 2:
            return 0.0

        returns = fund_data['unit_nav'].pct_change().dropna()

        if len(returns) < period:
            return 0.0

        volatility = returns.std() * np.sqrt(252 / len(returns))
        return float(volatility) if not np.isnan(volatility) else 0.0

    def calculate_sharpe_ratio(self, fund_code: str, risk_free_rate: float = 0.03) -> float:
        """计算夏普比率"""
        fund_data = self.nav_history[
            self.nav_history['fund_code'] == fund_code
        ].sort_values('date')

        if len(fund_data) < 2:
            return 0.0

        returns = fund_data['unit_nav'].pct_change().dropna()
        excess_returns = returns - risk_free_rate / 252

        if len(excess_returns) < 2:
            return 0.0

        return float(
            excess_returns.mean() / excess_returns.std() * np.sqrt(252)
            if not np.isnan(_) else 0.0
        )
```

### 3. 因子标准化

```python
# factors/standardizer.py
import pandas as pd
import numpy as np

def winsorize(series: pd.Series, lower_pct: float = 0.01, upper_pct: float = 0.99) -> pd.Series:
    """异常值处理：Winsorize"""
    lower = series.quantile(lower_pct)
    upper = series.quantile(upper_pct)
    return series.clip(lower, upper)

def standardize_by_category(values: np.ndarray, categories: np.ndarray) -> np.ndarray:
    """按类别标准化（Z-score）"""
    standardized = np.zeros_like(values)

    for category in np.unique(categories):
        mask = categories == category
        category_values = values[mask]

        if len(category_values) == 0:
            continue

        mean = category_values.mean()
        std = category_values.std()

        if std > 0:
            standardized[mask] = (category_values - mean) / std
        else:
            standardized[mask] = 0.0

    return standardized

def handle_missing_values(df: pd.DataFrame, strategy: str = 'median') -> pd.DataFrame:
    """缺失值处理"""
    if strategy == 'median':
        # 按类别填充中位数
        return df.groupby('category').transform(lambda x: x.fillna(x.median()))
    elif strategy == 'drop':
        # 删除含缺失值的行
        return df.dropna()
    elif strategy == 'forward_fill':
        # 前向填充
        return df.fillna(method='ffill')
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
```

### 4. 政策数据系统

```python
# policy/models.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

class PolicyEvent(BaseModel):
    policy_id: str = Field(..., description="政策ID")
    title: str = Field(..., description="政策标题")
    published_at: datetime = Field(..., description="发布时间")
    effective_from: datetime | None = Field(None, description="生效时间")
    related_sectors: list[str] = Field(..., description="关联行业")
    intensity_level: int = Field(..., ge=1, le=5, description="强度等级")
    execution_status: Literal['announced', 'detailed', 'implementing', 'completed'] = Field(
        default='announced', description="执行状态"
    )
    impact_direction: Literal['positive', 'negative', 'neutral'] = Field(
        default='neutral', description="影响方向"
    )
    description: str | None = Field(None, description="政策描述")

# policy/scoring.py
def calculate_policy_score(event: PolicyEvent) -> tuple[float, float, float]:
    """
    计算政策分数

    Returns:
        (support_score, execution_score, regulation_score)
    """
    # 支持强度评分（0-100）
    support_score = event.intensity_level * 20  # 1-5 级 -> 20-100分

    # 执行进度评分（0-100）
    execution_progress = {
        'announced': 10,
        'detailed': 30,
        'implementing': 60,
        'completed': 100,
    }[event.execution_status]
    execution_score = execution_progress

    # 监管安全度评分（0-100）
    if event.impact_direction == 'positive':
        regulation_score = 80
    elif event.impact_direction == 'negative':
        regulation_score = 40
    else:
        regulation_score = 60

    return (support_score, execution_score, regulation_score)
```

---

## 📁 文件结构

### 新增/修改文件

```
backend/app/
├── database_adapter.py        # NEW: 数据库抽象层
├── factors/
│   ├── __init__.py
│   ├── calculator.py           # NEW: 因子计算引擎
│   └── standardizer.py         # NEW: 因子标准化
├── policy/
│   ├── __init__.py
│   ├── models.py              # NEW: 政策数据模型
│   └── scoring.py              # NEW: 政策评分逻辑
├── utils/
│   ├── __init__.py
│   ├── cache.py               # NEW: 缓存工具
│   └── logging.py             # NEW: 日志工具
├── db.py                      # MODIFY: 使用适配器
├── store.py                   # MODIFY: 使用适配器
├── universe.py                # MODIFY: 调用真实计算
└── main.py                    # MODIFY: 集成新功能

docs/
├── SETUP.md                  # NEW: 安装指南
├── MIGRATION.md               # NEW: 迁移指南
├── API.md                     # NEW: API 文档
├── DEPLOYMENT.md              # NEW: 部署指南
└── ARCHITECTURE.md            # NEW: 架构设计

database/
├── schema_sqlite.sql          # NEW: SQLite Schema
├── schema_mysql.sql           # NEW: MySQL Schema
└── migrations/               # NEW: 迁移脚本
    ├── 001_add_history_tables.sql
    ├── 002_add_policy_tables.sql
    └── 003_add_indexes.sql
```

---

## ⚙️ 配置管理

### 环境变量

```bash
# .env.example
# 数据库类型（sqlite/mysql）
DB_TYPE=sqlite

# SQLite 配置
SQLITE_DB_PATH=fund_selection.db

# MySQL 配置
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=fund_selection

# Redis 配置（可选）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 数据源配置
AKSHARE_ENABLED=true
MARKET_UPDATE_INTERVAL_MINUTES=30

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 配置文件

```python
# config.py
import os
from functools import lru_cache
from typing import Literal

@lru_cache(maxsize=1)
def get_config():
    return Config(
        db_type=os.getenv("DB_TYPE", "sqlite"),
        sqlite_path=os.getenv("SQLITE_DB_PATH", "fund_selection.db"),
        mysql_host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        mysql_port=int(os.getenv("MYSQL_PORT", "3306")),
        mysql_user=os.getenv("MYSQL_USER", "root"),
        mysql_password=os.getenv("MYSQL_PASSWORD", "root"),
        mysql_database=os.getenv("MYSQL_DATABASE", "fund_selection"),

        redis_host=os.getenv("REDIS_HOST", "localhost"),
        redis_port=int(os.getenv("REDIS_PORT", "6379")),

        akshare_enabled=os.getenv("AKSHARE_ENABLED", "true").lower() == "true",
        market_update_interval_minutes=int(os.getenv("MARKET_UPDATE_INTERVAL_MINUTES", "30")),

        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )

class Config:
    def __init__(self, **kwargs):
        self.db_type: str = kwargs.get("db_type", "sqlite")
        self.sqlite_path: str = kwargs.get("sqlite_path", "fund_selection.db")
        self.mysql_host: str = kwargs.get("mysql_host", "127.0.0.1")
        # ... 其他配置
```

---

## 🧪 测试策略

### 单元测试

```python
# tests/test_factor_calculator.py
def test_calculate_annual_return():
    """测试年化收益率计算"""
    # 准备测试数据
    nav_history = pd.DataFrame({
        'fund_code': ['000001'] * 252,
        'date': pd.date_range('2025-01-01', periods=252),
        'unit_nav': [1.0 + i * 0.001 for i in range(252)]
    })

    calculator = FactorCalculator(nav_history)
    result = calculator.calculate_annual_return('000001', years=[1])

    assert '1y_return' in result
    assert abs(result['1y_return'] - 0.28) < 0.01  # 约28%年收益

def test_calculate_max_drawdown():
    """测试最大回撤计算"""
    nav_history = pd.DataFrame({
        'fund_code': ['000001'] * 10,
        'date': pd.date_range('2025-01-01', periods=10),
        'unit_nav': [1.0, 1.05, 1.03, 0.98, 0.95, 0.92, 0.94, 0.96, 0.99, 1.02]
    })

    calculator = FactorCalculator(nav_history)
    max_dd = calculator.calculate_max_drawdown('000001')

    assert max_dd < 0  # 应该是负值
    assert abs(max_dd - (-0.086)) < 0.01  # 约8.6%最大回撤
```

### 集成测试

```python
# tests/integration/test_data_flow.py
def test_full_data_flow():
    """测试完整数据流"""
    # 1. 获取历史数据
    nav_data = fetch_fund_nav_history('510300')
    assert len(nav_data) > 0

    # 2. 计算因子
    calculator = FactorCalculator(nav_data)
    factors = calculator.calculate_all_factors('510300')
    assert all(0 <= v <= 100 for v in factors.values())

    # 3. 存储到数据库
    adapter = create_adapter()
    adapter.insert_on_duplicate('funds', {...}, 'code')

    # 4. 通过 API 查询
    response = client.get(f"/api/v1/funds/510300")
    assert response.status_code == 200
    assert response.json()['final_score'] > 0
```

---

## 📈 性能指标

### 目标指标

| 指标 | 当前值 | 目标值 | 测量方法 |
|------|--------|--------|----------|
| API 响应时间 | ~200ms | <100ms | P95 |
| 因子计算时间 | N/A | <5s/基金 | 单次计算 |
| 数据库查询时间 | ~500ms | <100ms | P95 |
| 缓存命中率 | 0% | >80% | 监控 |
| 并发支持 | ~10 | ~100 | 并发用户 |

### 监控指标

```python
# prometheus_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# API 请求计数
api_request_counter = Counter(
    'api_requests_total',
    ['endpoint', 'method', 'status']
)

# API 响应时间
api_response_time = Histogram(
    'api_response_seconds',
    ['endpoint']
)

# 因子计算时间
factor_calculation_time = Histogram(
    'factor_calcuration_seconds',
    ['fund_type']
)

# 数据库连接池
db_pool_size = Gauge('db_pool_size')
```

---

## 🚨 风险控制

### 数据质量风险

**风险**: akshare 数据可能不准确或缺失

**缓解措施**:
1. 数据验证：检查价格范围、涨跌幅合理性
2. 多源验证：对比多个数据源
3. 异常检测：标记异常数据点
4. 人工审核：定期检查数据质量

### 性能风险

**风险**: 因子计算可能很慢

**缓解措施**:
1. 计算结果缓存：因子计算后存储到数据库
2. 增量更新：只更新变化的数据
3. 异步计算：后台任务定期更新因子
4. 降级策略：计算失败时使用缓存值

### 迁移风险

**风险**: 数据迁移可能丢失数据

**缓解措施**:
1. 备份原数据库
2. 先在测试环境验证
3. 分批迁移（每次 1000 只基金）
4. 回滚机制

---

## ✅ 验收标准

### Phase 1 验收
- ✅ SQLite 和 MySQL 可以通过环境变量切换
- ✅ 所有测试通过
- ✅ 迁移脚本执行成功
- ✅ 查询性能提升 50%+

### Phase 2 验收
- ✅ 所有因子都是真实计算
- ✅ 与 akshare 数据对比验证
- ✅ 计算性能 < 5秒/基金
- ✅ 单元测试覆盖率 > 90%

### Phase 3 验收
- ✅ 政策事件表有真实数据
- ✅ 政策分数基于真实事件计算
- ✅ 支持 CRUD 操作
- ✅ 与评分系统正常集成

### Phase 4 验收
- ✅ API 响应时间 < 500ms（P95）
- ✅ 数据更新不阻塞 API
- ✅ 缓存命中率 > 80%
- ✅ 错误有完整日志

### Phase 5 验收
- ✅ 测试覆盖率 > 80%
- ✅ 文档完整且清晰
- ✅ 可以一键部署
- ✅ 性能满足预期

---

## 📚 参考资料

### 技术文档
- [akshare 官方文档](https://akshare.akfamily.xyz/)
- [SQLite 文档](https://www.sqlite.org/docs.html)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Pandas 文档](https://pandas.pydata.org/)

### 项目文档
- `PRD.md` - 产品需求文档
- `DESIGN-SYSTEM.md` - 设计系统文档
- `COMPONENT-LIBRARY.md` - 组件库文档

---

## 🎯 下一步行动

1. **立即开始**：创建数据库适配器层
2. **本周启动**：实现历史数据表
3. **下周启动**：实现因子计算引擎
4. **持续优化**：监控性能，持续改进

---

**计划制定时间**: 2026-03-30
**预计完成时间**: 2026-05-25 (6-8周)
**负责人**: Claude (OMC Planning Agent)
**审批状态**: 待审批
