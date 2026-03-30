# 系统架构文档

目标受众：架构师和高级开发人员

## 1. 高级架构概览

### 1.1 系统架构图

```ascii
┌─────────────────────────────────────────────────────────────────────────┐
│                          用户界面层 (Frontend)                          │
├─────────────────────────────────────────────────────────────────────────┤
│  React + TypeScript + TailwindCSS                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  基金列表   │  │  基金详情   │  │  自选列表   │  │  对比分析   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        API 网关层 (Gateway)                             │
├─────────────────────────────────────────────────────────────────────────┤
│  FastAPI + CORS + 认证 (未来)                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ 路由管理   │  │ 参数验证   │  │ 响应格式化  │  │ 限流控制   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        业务逻辑层 (Business Logic)                      │
├─────────────────────────────────────────────────────────────────────────┤
│  核心业务模块                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  基金管理   │  │  评分系统   │  │  市场数据   │  │  自选服务   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  数据同步   │  │  政策分析   │  │  监控告警   │  │  日志记录   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        数据访问层 (Data Access)                          │
├─────────────────────────────────────────────────────────────────────────┤
│  数据库适配器 + 缓存管理                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  MySQL      │  │   Redis     │  │   SQLite    │  │ 文件存储    │ │
│  │  主数据库   │  │   缓存      │  │  开发环境   │  │  日志文件   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        数据源层 (Data Sources)                          │
├─────────────────────────────────────────────────────────────────────────┤
│  外部数据源集成                                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  akshare    │  │  数据库     │  │  API接口    │  │  文件数据   │ │
│  │  市场数据   │  │  基金数据   │  │  基准数据   │  │  历史数据   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈

| 层次 | 技术选型 | 用途 |
|------|----------|------|
| **前端** | React 18 + TypeScript + TailwindCSS | 用户界面组件 |
| **API网关** | FastAPI + CORS | HTTP API服务 |
| **业务逻辑** | Python 3.11+ | 核心业务处理 |
| **数据访问** | SQLAlchemy + MySQL | 数据库操作 |
| **缓存** | Redis (可选) | 性能优化 |
| **数据源** | akshare + API | 外部数据获取 |

### 1.3 架构原则

- **分层架构**：清晰的职责分离
- **微服务就绪**：模块化设计便于未来拆分
- **可扩展性**：支持横向扩展和负载均衡
- **高可用性**：容错设计和故障恢复
- **安全性**：多层安全防护
- **可维护性**：标准化和自动化

## 2. 数据流设计

### 2.1 核心数据流

```ascii
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  数据源     │    │  数据获取   │    │  数据处理   │    │  数据存储   │
├─────────────┤    ├─────────────┤    ├─────────────┤    ├─────────────┤
│ • akshare   │───▶│ • 实时获取  │───▶│ • 数据清洗  │───▶│ • MySQL     │
│ • 数据库    │    │ • 批量同步  │    │ • 格式转换  │    │ • Redis     │
│ • API接口   │    │ • 错误处理  │    │ • 验证校验  │    │ • 文件存储  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │
       ▼                  ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  基金数据   │    │  因子计算   │    │  评分系统   │    │  应用服务   │
├─────────────┤    ├─────────────┤    ├─────────────┤    ├─────────────┤
│ • 基金信息  │───▶│ • 收益因子  │───▶│ • 基础评分  │───▶│ • API服务   │
│ • 净值历史  │    │ • 风险因子  │    │ • 政策评分  │    │ • 前端应用   │
│ • 市场数据  │    │ • 稳定性    │    │ • 综合评分  │    │ • 数据展示   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### 2.2 详细数据流

#### 2.2.1 基金数据流

```python
# 基金数据流程
def fund_data_pipeline():
    """
    基金数据完整处理流程
    """
    # 1. 数据获取
    raw_data = fetch_fund_data()

    # 2. 数据清洗
    cleaned_data = clean_fund_data(raw_data)

    # 3. 数据验证
    validated_data = validate_fund_data(cleaned_data)

    # 4. 数据存储
    store_fund_data(validated_data)

    # 5. 数据同步
    sync_fund_universe()
```

#### 2.2.2 因子计算流

```python
# 因子计算流程
def factor_calculation_pipeline():
    """
    因子计算完整流程
    """
    # 1. 数据准备
    nav_history = get_nav_history()
    market_data = get_market_data()

    # 2. 因子计算
    factors = calculate_factors(nav_history, market_data)

    # 3. 标准化处理
    standardized_factors = standardize_factors(factors)

    # 4. 质量检查
    validated_factors = validate_factors(standardized_factors)

    # 5. 数据存储
    store_factors(validated_factors)
```

#### 2.2.3 评分计算流

```python
# 评分计算流程
def scoring_pipeline():
    """
    评分计算完整流程
    """
    # 1. 获取基础数据
    funds = get_funds()
    factors = get_factors()

    # 2. 基础评分
    base_scores = calculate_base_scores(funds, factors)

    # 3. 政策评分
    policy_scores = calculate_policy_scores(funds)

    # 4. 综合评分
    final_scores = calculate_final_scores(base_scores, policy_scores)

    # 5. 结果存储
    store_scores(final_scores)
```

## 3. 组件详细设计

### 3.1 数据库适配器层

#### 3.1.1 架构设计

```python
# database_adapter.py 核心设计
class DatabaseAdapter:
    """数据库适配器基类"""

    def __init__(self, config: dict):
        self.config = config
        self.engine = None
        self.session_factory = None

    def connect(self) -> bool:
        """建立数据库连接"""
        pass

    def execute(self, query: str, params: dict = None) -> ResultProxy:
        """执行SQL查询"""
        pass

    def get_tables(self) -> List[str]:
        """获取所有表名"""
        pass

class MySQLAdapter(DatabaseAdapter):
    """MySQL适配器实现"""

    def __init__(self, config: dict):
        super().__init__(config)
        self._init_mysql()

    def _init_mysql(self):
        """初始化MySQL连接"""
        from sqlalchemy import create_engine
        self.engine = create_engine(
            f"mysql+pymysql://{self.config['user']}:{self.config['password']}"
            f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
        )
        self.session_factory = sessionmaker(bind=self.engine)

class SQLiteAdapter(DatabaseAdapter):
    """SQLite适配器实现"""

    def __init__(self, config: dict):
        super().__init__(config)
        self._init_sqlite()

    def _init_sqlite(self):
        """初始化SQLite连接"""
        from sqlalchemy import create_engine
        self.engine = create_engine(f"sqlite:///{self.config['database_file']}")
        self.session_factory = sessionmaker(bind=self.engine)
```

#### 3.1.2 数据库模式

```sql
-- 基金表
CREATE TABLE funds (
    code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    channel ENUM('场内', '场外') NOT NULL,
    category VARCHAR(50) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    liquidity_label VARCHAR(50),
    years DECIMAL(10, 2),
    scale_billion DECIMAL(15, 2),
    one_year_return DECIMAL(10, 2),
    max_drawdown DECIMAL(10, 2),
    fee DECIMAL(5, 2),
    tracking_error DECIMAL(5, 2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 净值历史表
CREATE TABLE nav_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fund_code VARCHAR(20) NOT NULL,
    nav_date DATE NOT NULL,
    nav DECIMAL(15, 6) NOT NULL,
    nav_return DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_fund_code_nav_date (fund_code, nav_date),
    INDEX idx_fund_code (fund_code),
    INDEX idx_nav_date (nav_date)
);

-- 因子指标表
CREATE TABLE factor_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fund_code VARCHAR(20) NOT NULL,
    returns DECIMAL(10, 2) NOT NULL,
    risk_control DECIMAL(10, 2) NOT NULL,
    risk_adjusted DECIMAL(10, 2) NOT NULL,
    stability DECIMAL(10, 2) NOT NULL,
    cost_efficiency DECIMAL(10, 2) NOT NULL,
    liquidity DECIMAL(10, 2) NOT NULL,
    survival_quality DECIMAL(10, 2) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_fund_code (fund_code),
    INDEX idx_calculated_at (calculated_at)
);

-- 政策指标表
CREATE TABLE policy_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    policy_id VARCHAR(50) NOT NULL,
    fund_code VARCHAR(20) NOT NULL,
    support DECIMAL(10, 2) NOT NULL,
    execution DECIMAL(10, 2) NOT NULL,
    regulation_safety DECIMAL(10, 2) NOT NULL,
    effective_from DATE NOT NULL,
    expires_on DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_fund_code_policy (fund_code, policy_id),
    INDEX idx_policy_id (policy_id),
    INDEX idx_effective_from (effective_from)
);

-- 基准数据表
CREATE TABLE benchmarks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fund_code VARCHAR(20) NOT NULL,
    benchmark_name VARCHAR(100) NOT NULL,
    information_ratio DECIMAL(10, 4),
    upside_capture DECIMAL(10, 4),
    downside_capture DECIMAL(10, 4),
    tracking_error DECIMAL(10, 4),
    sharpe_ratio DECIMAL(10, 4),
    sortino_ratio DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_fund_code (fund_code),
    INDEX idx_benchmark_name (benchmark_name)
);

-- 自选表
CREATE TABLE watchlist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    fund_code VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_fund (user_id, fund_code),
    INDEX idx_user_id (user_id),
    INDEX idx_fund_code (fund_code)
);
```

### 3.2 NAV历史管理器

#### 3.2.1 设计模式

```python
# data/nav_history.py
class NAVHistoryManager:
    """NAV历史管理器 - 单例模式"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.db = Database()
        self.cache = TTLCache(maxsize=1000, ttl=3600)

    def fetch_nav_history(self, fund_code: str, start_date: str, end_date: str) -> List[NAVRecord]:
        """获取NAV历史数据"""
        # 检查缓存
        cache_key = f"{fund_code}_{start_date}_{end_date}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # 从数据库获取
        records = self.db.get_nav_history(fund_code, start_date, end_date)

        # 缓存结果
        self.cache[cache_key] = records

        return records

    def backfill_nav_history(self, fund_code: str, years: int = 3) -> Dict[str, Any]:
        """回填NAV历史数据"""
        # 从akshare获取数据
        akshare_data = fetch_akshare_nav_data(fund_code, years)

        # 数据清洗
        cleaned_data = clean_nav_data(akshare_data)

        # 批量插入数据库
        result = self.db.batch_insert_nav_history(cleaned_data)

        return result

    def calculate_nav_returns(self, nav_history: List[NAVRecord]) -> Dict[str, float]:
        """计算NAV收益率"""
        returns = {}

        if len(nav_history) < 2:
            return returns

        # 计算日收益率
        for i in range(1, len(nav_history)):
            prev_nav = nav_history[i-1].nav
            curr_nav = nav_history[i].nav
            daily_return = (curr_nav - prev_nav) / prev_nav
            returns[nav_history[i].nav_date] = daily_return

        # 计算年化收益率
        annual_return = calculate_annual_return(returns)
        returns['annual'] = annual_return

        return returns
```

#### 3.2.2 数据质量保证

```python
# 数据验证器
class DataValidator:
    """数据质量验证器"""

    @staticmethod
    def validate_nav_data(nav_data: List[dict]) -> ValidationResult:
        """验证NAV数据质量"""
        errors = []
        warnings = []

        # 检查数据完整性
        if not nav_data:
            errors.append("NAV数据为空")
            return ValidationResult(errors=errors, warnings=warnings)

        # 检查日期连续性
        dates = [record['nav_date'] for record in nav_data]
        if not DataValidator._check_date_continuity(dates):
            warnings.append("NAV数据日期不连续")

        # 检查数值合理性
        for record in nav_data:
            nav = record['nav']
            if nav <= 0:
                errors.append(f"NAV值不合理: {nav}")
            if nav > 10:  # 假设NAV不应该超过10
                warnings.append(f"NAV值异常高: {nav}")

        return ValidationResult(errors=errors, warnings=warnings)

    @staticmethod
    def _check_date_continuity(dates: List[str]) -> bool:
        """检查日期连续性"""
        if len(dates) < 2:
            return True

        sorted_dates = sorted(dates)
        for i in range(1, len(sorted_dates)):
            prev_date = datetime.strptime(sorted_dates[i-1], '%Y-%m-%d')
            curr_date = datetime.strptime(sorted_dates[i], '%Y-%m-%d')
            days_diff = (curr_date - prev_date).days

            # 允许周末跳过
            if days_diff > 3:  # 周末+节假日
                return False

        return True
```

### 3.3 因子计算器

#### 3.3.1 因子计算架构

```python
# factors/calculator.py
class FactorCalculator:
    """因子计算引擎"""

    def __init__(self):
        self.nav_history = NAVHistoryManager()
        self.benchmark_manager = BenchmarkManager()
        self.cache = TTLCache(maxsize=1000, ttl=1800)  # 30分钟缓存

    def calculate_all_factors(self, fund_code: str) -> FactorMetrics:
        """计算所有因子"""
        # 检查缓存
        cache_key = f"all_factors_{fund_code}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # 获取NAV历史数据
        nav_history = self.nav_history.fetch_nav_history(
            fund_code,
            start_date=(datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d'),
            end_date=datetime.now().strftime('%Y-%m-%d')
        )

        # 计算各个因子
        returns = self._calculate_returns_factor(nav_history)
        risk_control = self._calculate_risk_control_factor(nav_history)
        risk_adjusted = self._calculate_risk_adjusted_factor(nav_history)
        stability = self._calculate_stability_factor(nav_history)
        cost_efficiency = self._calculate_cost_efficiency_factor(fund_code)
        liquidity = self._calculate_liquidity_factor(nav_history)
        survival_quality = self._calculate_survival_quality_factor(fund_code)

        # 构建结果
        factors = FactorMetrics(
            returns=returns,
            risk_control=risk_control,
            risk_adjusted=risk_adjusted,
            stability=stability,
            cost_efficiency=cost_efficiency,
            liquidity=liquidity,
            survival_quality=survival_quality
        )

        # 缓存结果
        self.cache[cache_key] = factors

        return factors

    def _calculate_returns_factor(self, nav_history: List[NAVRecord]) -> float:
        """计算收益率因子"""
        if len(nav_history) < 2:
            return 0.0

        # 计算年化收益率
        returns = self.nav_history.calculate_nav_returns(nav_history)
        annual_return = returns.get('annual', 0.0)

        # 转换为0-100分的评分
        # 假设年化15%得100分，0%得0分
        score = min(100, max(0, annual_return * 1000 / 15))

        return round(score, 2)

    def _calculate_risk_control_factor(self, nav_history: List[NAVRecord]) -> float:
        """计算风险控制因子"""
        if len(nav_history) < 2:
            return 0.0

        # 计算最大回撤
        max_drawdown = self._calculate_max_drawdown(nav_history)

        # 转换为0-100分的评分
        # 假设最大回撤-5%得100分，-20%得0分
        score = min(100, max(0, (20 - abs(max_drawdown)) * 5))

        return round(score, 2)

    def _calculate_risk_adjusted_factor(self, nav_history: List[NAVRecord]) -> float:
        """计算风险调整收益因子"""
        if len(nav_history) < 2:
            return 0.0

        # 计算夏普比率
        returns = self.nav_history.calculate_nav_returns(nav_history)
        sharpe_ratio = self._calculate_sharpe_ratio(returns)

        # 转换为0-100分的评分
        # 假设夏普比率2.0得100分，0得0分
        score = min(100, max(0, sharpe_ratio * 50))

        return round(score, 2)

    def _calculate_stability_factor(self, nav_history: List[NAVRecord]) -> float:
        """计算稳定性因子"""
        if len(nav_history) < 30:  # 至少需要30天数据
            return 0.0

        # 计算收益率的波动率
        returns = self.nav_history.calculate_nav_returns(nav_history)
        volatility = np.std(list(returns.values())[:-1]) if len(returns) > 1 else 0

        # 转换为0-100分的评分
        # 假设波动率5%得100分，20%得0分
        score = min(100, max(0, (20 - volatility) * 5))

        return round(score, 2)

    def _calculate_cost_efficiency_factor(self, fund_code: str) -> float:
        """计算成本效率因子"""
        # 获取基金费率
        fund = get_fund(fund_code)
        if not fund:
            return 0.0

        # 计算费率评分
        # 假设费率0.5%得100分，2.0%得0分
        fee_score = min(100, max(0, (2.0 - fund.fee) * 50))

        # 考虑费用比
        expense_ratio = fund.expense_ratio if hasattr(fund, 'expense_ratio') else 0.0
        expense_score = min(100, max(0, (1.0 - expense_ratio) * 100))

        # 综合评分
        total_score = (fee_score * 0.7 + expense_score * 0.3)

        return round(total_score, 2)

    def _calculate_liquidity_factor(self, nav_history: List[NAVRecord]) -> float:
        """计算流动性因子"""
        if len(nav_history) < 30:
            return 0.0

        # 计算换手率（基于NAV变化频率）
        nav_changes = sum(1 for i in range(1, len(nav_history))
                         if abs(nav_history[i].nav - nav_history[i-1].nav) > 0.001)

        # 转换为0-100分的评分
        liquidity_ratio = nav_changes / len(nav_history)
        score = min(100, max(0, liquidity_ratio * 1000))

        return round(score, 2)

    def _calculate_survival_quality_factor(self, fund_code: str) -> float:
        """计算存续质量因子"""
        # 获取基金运作年限
        fund = get_fund(fund_code)
        if not fund:
            return 0.0

        # 计算运作年限评分
        # 假设3年得100分，0.5年得0分
        years_score = min(100, max(0, fund.years * 33.33))

        # 考虑基金规模
        scale_score = min(100, max(0, fund.scale_billion / 100))

        # 综合评分
        total_score = (years_score * 0.7 + scale_score * 0.3)

        return round(total_score, 2)
```

#### 3.3.2 因子标准化

```python
# factors/standardizer.py
class FactorStandardizer:
    """因子标准化器"""

    def __init__(self):
        self.cache = {}

    def standardize_factors(self, factors: List[FactorMetrics]) -> List[FactorMetrics]:
        """批量标准化因子"""
        # 计算统计量
        stats = self._calculate_statistics(factors)

        # 标准化每个因子
        standardized = []
        for factor in factors:
            standardized_factor = self._standardize_single_factor(factor, stats)
            standardized.append(standardized_factor)

        return standardized

    def _calculate_statistics(self, factors: List[FactorMetrics]) -> Dict[str, Dict]:
        """计算因子统计量"""
        if not factors:
            return {}

        stats = {}
        factor_names = ['returns', 'risk_control', 'risk_adjusted', 'stability',
                       'cost_efficiency', 'liquidity', 'survival_quality']

        for name in factor_names:
            values = [getattr(factor, name) for factor in factors]
            stats[name] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values)
            }

        return stats

    def _standardize_single_factor(self, factor: FactorMetrics,
                                  stats: Dict[str, Dict]) -> FactorMetrics:
        """标准化单个因子"""
        # 创建新的因子对象
        standardized_factor = FactorMetrics(
            returns=self._z_score_standardization(factor.returns, stats['returns']),
            risk_control=self._z_score_standardization(factor.risk_control, stats['risk_control']),
            risk_adjusted=self._z_score_standardization(factor.risk_adjusted, stats['risk_adjusted']),
            stability=self._z_score_standardization(factor.stability, stats['stability']),
            cost_efficiency=self._z_score_standardization(factor.cost_efficiency, stats['cost_efficiency']),
            liquidity=self._z_score_standardization(factor.liquidity, stats['liquidity']),
            survival_quality=self._z_score_standardization(factor.survival_quality, stats['survival_quality'])
        )

        return standardized_factor

    def _z_score_standardization(self, value: float, stats: Dict) -> float:
        """Z-score标准化"""
        if stats['std'] == 0:
            return 50  # 如果标准差为0，返回中间值

        z_score = (value - stats['mean']) / stats['std']
        # 将Z-score转换为0-100分的评分
        standardized_score = 50 + z_score * 15  # 假设1个标准差=15分

        return max(0, min(100, round(standardized_score, 2)))
```

### 3.4 政策评分系统

#### 3.4.1 政策评估框架

```python
# policy/models.py
class PolicyEvaluator:
    """政策评估器"""

    def __init__(self):
        self.policy_db = PolicyDatabase()
        self.cache = TTLCache(maxsize=500, ttl=1800)

    def evaluate_policy_impact(self, fund: Fund,
                              policies: List[Policy]) -> PolicyMetrics:
        """评估政策对基金的影响"""

        policy_metrics = PolicyMetrics(
            support=0.0,
            execution=0.0,
            regulation_safety=0.0
        )

        # 评估每个政策的影响
        for policy in policies:
            impact = self._evaluate_single_policy(fund, policy)
            policy_metrics.support += impact.support
            policy_metrics.execution += impact.execution
            policy_metrics.regulation_safety += impact.regulation_safety

        # 平均化
        num_policies = len(policies)
        if num_policies > 0:
            policy_metrics.support /= num_policies
            policy_metrics.execution /= num_policies
            policy_metrics.regulation_safety /= num_policies

        return policy_metrics

    def _evaluate_single_policy(self, fund: Fund, policy: Policy) -> PolicyMetrics:
        """评估单个政策的影响"""

        # 政策支持度评估
        support_score = self._evaluate_policy_support(fund, policy)

        # 政策执行度评估
        execution_score = self._evaluate_policy_execution(fund, policy)

        # 监管安全度评估
        regulation_score = self._evaluate_regulation_safety(fund, policy)

        return PolicyMetrics(
            support=support_score,
            execution=execution_score,
            regulation_safety=regulation_score
        )

    def _evaluate_policy_support(self, fund: Fund, policy: Policy) -> float:
        """评估政策支持度"""
        # 基金类别与政策的相关性
        category_alignment = self._get_category_policy_alignment(fund.category, policy)

        # 政策发布时间的影响
        time_weight = self._get_policy_time_weight(policy)

        # 基金规模的影响
        scale_weight = self._get_fund_scale_weight(fund.scale_billion)

        # 综合评分
        support_score = (category_alignment * 0.5 +
                         time_weight * 0.3 +
                         scale_weight * 0.2)

        return min(100, max(0, support_score))

    def _evaluate_policy_execution(self, fund: Fund, policy: Policy) -> float:
        """评估政策执行度"""
        # 基金经理政策执行能力
        manager_execution = self._get_manager_execution_score(fund.manager_id)

        # 基金历史执行情况
        fund_execution = self._get_fund_execution_score(fund.code)

        # 政策复杂度调整
        complexity_adjustment = self._get_policy_complexity_adjustment(policy)

        # 综合评分
        execution_score = (manager_execution * 0.4 +
                          fund_execution * 0.4 +
                          complexity_adjustment * 0.2)

        return min(100, max(0, execution_score))

    def _evaluate_regulation_safety(self, fund: Fund, policy: Policy) -> float:
        """评估监管安全度"""
        # 基金合规历史
        compliance_score = self._get_compliance_score(fund.code)

        # 政策监管强度
        regulation_strength = self._get_policy_regulation_strength(policy)

        # 基金风险等级
        risk_adjustment = self._get_risk_adjustment(fund.risk_level)

        # 综合评分
        safety_score = (compliance_score * 0.5 +
                       regulation_strength * 0.3 +
                       risk_adjustment * 0.2)

        return min(100, max(0, safety_score))
```

#### 3.4.2 政策时间验证

```python
# policy_validation.py
class PolicyValidator:
    """政策时间验证器"""

    @staticmethod
    def validate_policy_timestamps(policy_id: str, published_at: datetime,
                                  effective_from: datetime, observed_at: datetime) -> tuple[bool, List[str]]:
        """验证政策时间戳的有效性"""
        errors = []

        # 验证时间顺序
        if published_at >= effective_from:
            errors.append("发布时间必须早于生效时间")

        if effective_from >= observed_at:
            errors.append("生效时间必须早于观察时间")

        # 验证时间合理性
        now = datetime.now()
        if published_at > now:
            errors.append("发布时间不能晚于当前时间")

        # 验证时间间隔
        if (effective_from - published_at).days > 365:
            errors.append("发布到生效的间隔不能超过365天")

        if (observed_at - effective_from).days > 30:
            errors.append("生效到观察的间隔不能超过30天")

        return len(errors) == 0, errors

    @staticmethod
    def validate_policy_effectiveness(policy: Policy, observed_data: Dict) -> tuple[bool, List[str]]:
        """验证政策效果"""
        errors = []

        # 检查政策目标达成情况
        if policy.target_type == 'return':
            if observed_data.get('actual_return', 0) < policy.target_value:
                errors.append(f"未达成收益率目标: {policy.target_value}%")

        elif policy.target_type == 'risk':
            if observed_data.get('actual_risk', 100) > policy.target_value:
                errors.append(f"未控制风险目标: {policy.target_value}")

        # 检查政策执行情况
        if observed_data.get('execution_rate', 0) < 0.8:
            errors.append("政策执行率低于80%")

        return len(errors) == 0, errors
```

### 3.5 基准数据管理器

#### 3.5.1 基准计算引擎

```python
# benchmark/manager.py
class BenchmarkManager:
    """基准数据管理器"""

    def __init__(self):
        self.db = Database()
        self.cache = TTLCache(maxsize=1000, ttl=3600)

    def calculate_benchmarks(self, fund_code: str, benchmark_name: str = "沪深300") -> Dict[str, float]:
        """计算基金基准指标"""

        cache_key = f"benchmark_{fund_code}_{benchmark_name}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # 获取基金数据
        fund_data = self._get_fund_data(fund_code)

        # 获取基准数据
        benchmark_data = self._get_benchmark_data(benchmark_name)

        # 计算相对指标
        information_ratio = self._calculate_information_ratio(fund_data, benchmark_data)
        upside_capture = self._calculate_upside_capture(fund_data, benchmark_data)
        downside_capture = self._calculate_downside_capture(fund_data, benchmark_data)
        tracking_error = self._calculate_tracking_error(fund_data, benchmark_data)

        # 计算风险调整指标
        sharpe_ratio = self._calculate_sharpe_ratio(fund_data)
        sortino_ratio = self._calculate_sortino_ratio(fund_data)

        # 构建结果
        benchmarks = {
            'information_ratio': round(information_ratio, 4),
            'upside_capture': round(upside_capture, 4),
            'downside_capture': round(downside_capture, 4),
            'tracking_error': round(tracking_error, 4),
            'sharpe_ratio': round(sharpe_ratio, 4),
            'sortino_ratio': round(sortino_ratio, 4)
        }

        # 缓存结果
        self.cache[cache_key] = benchmarks

        return benchmarks

    def _calculate_information_ratio(self, fund_data: List[Dict],
                                   benchmark_data: List[Dict]) -> float:
        """计算信息比率"""
        # 计算相对收益率
        relative_returns = []
        for fund_return, benchmark_return in zip(fund_data, benchmark_data):
            relative_return = fund_return['return'] - benchmark_return['return']
            relative_returns.append(relative_return)

        # 计算平均相对收益率
        avg_relative_return = np.mean(relative_returns)

        # 计算跟踪误差
        tracking_error = np.std(relative_returns)

        if tracking_error == 0:
            return 0.0

        # 信息比率 = 平均相对收益率 / 跟踪误差
        information_ratio = avg_relative_return / tracking_error

        return information_ratio

    def _calculate_upside_capture(self, fund_data: List[Dict],
                                benchmark_data: List[Dict]) -> float:
        """计算上行捕获比率"""
        # 筛选出正收益的期间
        positive_periods = []
        for fund_return, benchmark_return in zip(fund_data, benchmark_data):
            if benchmark_return['return'] > 0:
                positive_periods.append({
                    'fund_return': fund_return['return'],
                    'benchmark_return': benchmark_return['return']
                })

        if not positive_periods:
            return 0.0

        # 计算上行捕获比率
        fund_upside = np.mean([p['fund_return'] for p in positive_periods])
        benchmark_upside = np.mean([p['benchmark_return'] for p in positive_periods])

        if benchmark_upside == 0:
            return 0.0

        upside_capture = (fund_upside / benchmark_upside) * 100

        return upside_capture

    def _calculate_downside_capture(self, fund_data: List[Dict],
                                   benchmark_data: List[Dict]) -> float:
        """计算下行捕获比率"""
        # 筛选出负收益的期间
        negative_periods = []
        for fund_return, benchmark_return in zip(fund_data, benchmark_data):
            if benchmark_return['return'] < 0:
                negative_periods.append({
                    'fund_return': fund_return['return'],
                    'benchmark_return': benchmark_return['return']
                })

        if not negative_periods:
            return 0.0

        # 计算下行捕获比率
        fund_downside = np.mean([p['fund_return'] for p in negative_periods])
        benchmark_downside = np.mean([p['benchmark_return'] for p in negative_periods])

        if benchmark_downside == 0:
            return 0.0

        downside_capture = abs(fund_downside / benchmark_downside) * 100

        return downside_capture

    def _calculate_tracking_error(self, fund_data: List[Dict],
                                benchmark_data: List[Dict]) -> float:
        """计算跟踪误差"""
        # 计算相对收益率
        relative_returns = []
        for fund_return, benchmark_return in zip(fund_data, benchmark_data):
            relative_return = fund_return['return'] - benchmark_return['return']
            relative_returns.append(relative_return)

        # 计算标准差
        tracking_error = np.std(relative_returns) * np.sqrt(252)  # 年化

        return tracking_error

    def _calculate_sharpe_ratio(self, fund_data: List[Dict]) -> float:
        """计算夏普比率"""
        if not fund_data:
            return 0.0

        # 计算平均收益率
        returns = [d['return'] for d in fund_data]
        avg_return = np.mean(returns)

        # 计算波动率
        volatility = np.std(returns)

        if volatility == 0:
            return 0.0

        # 夏普比率 = 平均收益率 / 波动率
        sharpe_ratio = avg_return / volatility

        return sharpe_ratio

    def _calculate_sortino_ratio(self, fund_data: List[Dict]) -> float:
        """计算索提诺比率"""
        if not fund_data:
            return 0.0

        # 计算平均收益率
        returns = [d['return'] for d in fund_data]
        avg_return = np.mean(returns)

        # 计算下行波动率
        downside_returns = [r for r in returns if r < 0]
        downside_volatility = np.std(downside_returns) if downside_returns else 0

        if downside_volatility == 0:
            return 0.0

        # 索提诺比率 = 平均收益率 / 下行波动率
        sortino_ratio = avg_return / downside_volatility

        return sortino_ratio
```

## 4. 缓存策略

### 4.1 缓存架构

```python
# 缓存配置
from datetime import timedelta
from cachetools import TTLCache

class CacheConfig:
    """缓存配置类"""

    # 内存缓存配置
    MEMORY_CACHE = {
        'maxsize': 1000,  # 最大缓存条目数
        'ttl': 3600,      # 缓存过期时间（秒）
    }

    # Redis缓存配置
    REDIS_CACHE = {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'expire': 3600,  # 过期时间（秒）
    }

    # 缓存键前缀
    CACHE_KEYS = {
        'funds': 'funds',
        'factors': 'factors',
        'benchmarks': 'benchmarks',
        'policy': 'policy',
        'market': 'market',
    }
```

### 4.2 缓存实现

```python
# 缓存管理器
class CacheManager:
    """缓存管理器"""

    def __init__(self):
        self.memory_cache = TTLCache(**CacheConfig.MEMORY_CACHE)
        self.redis_cache = Redis(**CacheConfig.REDIS_CACHE)

    def get_funds(self, key: str) -> Optional[List[Fund]]:
        """获取基金缓存"""
        cache_key = f"{CacheConfig.CACHE_KEYS['funds']}_{key}"

        # 先查内存缓存
        if cache_key in self.memory_cache:
            return self.memory_cache[cache_key]

        # 再查Redis缓存
        try:
            data = self.redis_cache.get(cache_key)
            if data:
                funds = json.loads(data)
                self.memory_cache[cache_key] = funds
                return funds
        except Exception:
            pass

        return None

    def set_funds(self, key: str, funds: List[Fund]) -> None:
        """设置基金缓存"""
        cache_key = f"{CacheConfig.CACHE_KEYS['funds']}_{key}"

        # 设置内存缓存
        self.memory_cache[cache_key] = funds

        # 设置Redis缓存
        try:
            data = json.dumps([f.model_dump() for f in funds])
            self.redis_cache.setex(cache_key, CacheConfig.REDIS_CACHE['expire'], data)
        except Exception:
            pass

    def invalidate_funds(self, fund_code: str = None) -> None:
        """失效基金缓存"""
        # 失效内存缓存
        keys_to_remove = [k for k in self.memory_cache.keys()
                         if CacheConfig.CACHE_KEYS['funds'] in k]
        for key in keys_to_remove:
            del self.memory_cache[key]

        # 失效Redis缓存
        try:
            if fund_code:
                pattern = f"{CacheConfig.CACHE_KEYS['funds']}_{fund_code}*"
                keys = self.redis_cache.keys(pattern)
                if keys:
                    self.redis_cache.delete(*keys)
            else:
                pattern = f"{CacheConfig.CACHE_KEYS['funds']}*"
                keys = self.redis_cache.keys(pattern)
                if keys:
                    self.redis_cache.delete(*keys)
        except Exception:
            pass
```

## 5. 性能优化

### 5.1 数据库优化

```python
# 数据库索引优化
INDEXES = [
    "CREATE INDEX idx_funds_category ON funds(category);",
    "CREATE INDEX idx_funds_risk_level ON funds(risk_level);",
    "CREATE INDEX idx_funds_updated_at ON funds(updated_at);",
    "CREATE INDEX idx_factors_fund_code ON factors(fund_code);",
    "CREATE INDEX idx_factors_calculated_at ON factors(calculated_at);",
    "CREATE INDEX idx_benchmarks_fund_code ON benchmarks(fund_code);",
    "CREATE INDEX idx_benchmarks_benchmark_name ON benchmarks(benchmark_name);",
    "CREATE INDEX idx_watchlist_user_id ON watchlist(user_id);",
    "CREATE INDEX idx_watchlist_fund_code ON watchlist(fund_code);",
]

# 查询优化
QUERY_OPTIMIZATIONS = {
    'get_funds': """
        SELECT f.*, fm.returns, fm.risk_control, fm.risk_adjusted
        FROM funds f
        LEFT JOIN factor_metrics fm ON f.code = fm.fund_code
        WHERE fm.calculated_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    """,

    'get_fund_detail': """
        SELECT f.*, fm.*, pm.*, b.*
        FROM funds f
        LEFT JOIN factor_metrics fm ON f.code = fm.fund_code
        LEFT JOIN policy_metrics pm ON f.code = pm.fund_code
        LEFT JOIN benchmarks b ON f.code = b.fund_code
        WHERE f.code = %s
    """
}
```

### 5.2 查询优化

```python
# 查询优化器
class QueryOptimizer:
    """查询优化器"""

    @staticmethod
    def optimize_fund_query(params: Dict) -> str:
        """优化基金查询"""
        base_query = """
        SELECT f.*, fm.returns, fm.risk_control, fm.risk_adjusted
        FROM funds f
        LEFT JOIN factor_metrics fm ON f.code = fm.fund_code
        WHERE 1=1
        """

        conditions = []
        if params.get('category'):
            conditions.append("f.category = %s")
        if params.get('risk_level'):
            conditions.append("f.risk_level = %s")
        if params.get('min_years'):
            conditions.append("f.years >= %s")
        if params.get('min_scale'):
            conditions.append("f.scale_billion >= %s")

        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        # 添加排序
        sort_by = params.get('sort_by', 'updated_at')
        sort_order = params.get('sort_order', 'DESC')
        base_query += f" ORDER BY f.{sort_by} {sort_order}"

        # 添加分页
        page = params.get('page', 1)
        page_size = params.get('page_size', 20)
        offset = (page - 1) * page_size
        base_query += f" LIMIT {offset}, {page_size}"

        return base_query

    @staticmethod
    def get_query_plan(query: str) -> Dict:
        """获取查询计划"""
        # 模拟查询计划分析
        return {
            'estimated_rows': 100,
            'estimated_cost': 0.1,
            'indexes_used': ['idx_funds_category', 'idx_factors_fund_code'],
            'execution_time': '0.01s'
        }
```

## 6. 安全设计

### 6.1 安全架构

```python
# 安全配置
class SecurityConfig:
    """安全配置"""

    # API密钥配置
    API_KEY = {
        'header': 'X-API-Key',
        'length': 32,
        'algorithm': 'sha256'
    }

    # 认证配置
    AUTH = {
        'algorithm': 'HS256',
        'expire_minutes': 1440,  # 24小时
        'issuer': 'fund-selection'
    }

    # 限流配置
    RATE_LIMIT = {
        'requests_per_minute': 100,
        'requests_per_hour': 1000,
        'burst_size': 20
    }

    # CORS配置
    CORS = {
        'allow_origins': ['https://your-domain.com'],
        'allow_methods': ['GET', 'POST', 'PUT', 'DELETE'],
        'allow_headers': ['*'],
        'allow_credentials': True
    }
```

### 6.2 数据加密

```python
# 数据加密器
class DataEncryptor:
    """数据加密器"""

    def __init__(self):
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)

    def encrypt_sensitive_data(self, data: str) -> str:
        """加密敏感数据"""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """解密敏感数据"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

    def hash_password(self, password: str) -> str:
        """密码哈希"""
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        return salt.hex() + key.hex()
```

## 7. 监控和日志

### 7.1 监控设计

```python
# 监控指标
class MonitoringMetrics:
    """监控指标"""

    def __init__(self):
        self.metrics = {}

    def record_api_request(self, endpoint: str, method: str,
                          status_code: int, response_time: float):
        """记录API请求"""
        key = f"api_{method}_{endpoint}"
        if key not in self.metrics:
            self.metrics[key] = {
                'count': 0,
                'total_time': 0.0,
                'error_count': 0
            }

        self.metrics[key]['count'] += 1
        self.metrics[key]['total_time'] += response_time

        if status_code >= 400:
            self.metrics[key]['error_count'] += 1

    def get_api_metrics(self) -> Dict:
        """获取API指标"""
        result = {}
        for key, data in self.metrics.items():
            result[key] = {
                'requests': data['count'],
                'avg_response_time': data['total_time'] / data['count'],
                'error_rate': data['error_count'] / data['count']
            }
        return result

    def record_database_query(self, query: str, execution_time: float,
                            success: bool):
        """记录数据库查询"""
        key = f"db_{hash(query)}"
        if key not in self.metrics:
            self.metrics[key] = {
                'count': 0,
                'total_time': 0.0,
                'error_count': 0
            }

        self.metrics[key]['count'] += 1
        self.metrics[key]['total_time'] += execution_time

        if not success:
            self.metrics[key]['error_count'] += 1
```

### 7.2 日志系统

```python
# 日志配置
import logging
from logging.handlers import RotatingFileHandler

class LogConfig:
    """日志配置"""

    @staticmethod
    def setup_logging():
        """设置日志系统"""
        # 创建日志目录
        os.makedirs('logs', exist_ok=True)

        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # 设置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # 文件处理器
        file_handler = RotatingFileHandler(
            'logs/app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        return root_logger

# 业务日志
logger = LogConfig.setup_logging()

class BusinessLogger:
    """业务日志记录器"""

    @staticmethod
    def log_fund_operation(operation: str, fund_code: str, user_id: str = None):
        """记录基金操作日志"""
        log_data = {
            'operation': operation,
            'fund_code': fund_code,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }
        logger.info(f"Fund Operation: {json.dumps(log_data)}")

    @staticmethod
    def log_api_request(request: Request, response: Response):
        """记录API请求日志"""
        log_data = {
            'method': request.method,
            'url': str(request.url),
            'user_agent': request.headers.get('user-agent'),
            'ip_address': request.client.host,
            'status_code': response.status_code,
            'response_time': response.headers.get('x-response-time'),
            'timestamp': datetime.now().isoformat()
        }
        logger.info(f"API Request: {json.dumps(log_data)}")
```

## 8. 部署架构

### 8.1 容器化架构

```dockerfile
# Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml .

# 安装Python依赖
RUN pip install --no-cache-dir -e .

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# 切换用户
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 8.2 Kubernetes配置

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fund-selection-backend
  namespace: fund-selection
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fund-selection-backend
  template:
    metadata:
      labels:
        app: fund-selection-backend
    spec:
      containers:
      - name: backend
        image: fund-selection-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DB_TYPE
          value: "mysql"
        - name: MYSQL_HOST
          value: "mysql-service"
        - name: MYSQL_PORT
          value: "3306"
        - name: MYSQL_USER
          value: "fund_user"
        - name: MYSQL_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: password
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: fund-selection-backend
  namespace: fund-selection
spec:
  selector:
    app: fund-selection-backend
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP
```

## 9. 总结

本架构文档提供了基金选择系统的完整架构设计，包括：

✅ **分层架构**：清晰的层次结构和职责分离
✅ **数据流设计**：完整的数据处理流程和管道
✅ **组件设计**：各个核心组件的详细实现
✅ **缓存策略**：多级缓存和失效机制
✅ **性能优化**：数据库优化、查询优化、性能监控
✅ **安全设计**：认证授权、数据加密、访问控制
✅ **监控日志**：完整的监控指标和日志系统
✅ **部署架构**：容器化和Kubernetes配置

该架构设计确保了系统的高性能、高可用性、可扩展性和可维护性，为基金选择系统提供了坚实的技术基础。