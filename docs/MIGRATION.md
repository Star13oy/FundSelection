# 迁移指南：从遗留系统到生产系统

目标受众：系统升级团队

## 1. 概述

### 1.1 迁移背景

本次迁移将基金选择系统从基于MD5哈希的简单评分系统升级为基于真实金融数学模型的生产级评分系统。

**主要变化**：
- **评分算法**：从MD5哈希 → 真实因子计算
- **数据来源**：从静态数据 → 实时市场数据
- **计算复杂度**：从简单 → 复杂金融模型
- **数据维度**：从单一指标 → 多因子综合评分

**为什么需要迁移**：
- 提供更准确的基金评估和选股建议
- 支持实时市场数据和历史回测
- 增强系统的生产级稳定性和可扩展性
- 符合金融行业的技术规范

### 1.2 迁移范围

| 组件 | 影响程度 | 迁移方式 |
|------|----------|----------|
| 核心评分算法 | 高 | 完全重写 |
| 数据存储 | 中 | 结构优化 |
| API接口 | 低 | 向后兼容 |
| 前端界面 | 低 | 兼容性保持 |
| 部署架构 | 高 | 容器化升级 |

### 1.3 向后兼容性

- **API兼容**：所有现有API端点保持兼容
- **数据结构**：数据库表结构保持兼容
- **配置迁移**：现有配置文件自动适配
- **平滑过渡**：可随时回退到原有系统

## 2. 迁移前准备

### 2.1 预检查清单

在开始迁移前，请确认以下事项：

```bash
# [ ] 备份现有数据库
mysql -u root -p -e "SHOW VARIABLES LIKE 'datadir';"

# [ ] 验证MySQL连接
mysql -u fund_user -p fund_selection -e "SELECT COUNT(*) FROM funds;"

# [ ] 检查磁盘空间
df -h /var/lib/mysql

# [ ] 备份应用程序代码
tar -czf /backup/fund-selection-pre-migration.tar.gz /opt/fund-selection

# [ ] 验证备份完整性
ls -la /backup/
md5sum /backup/fund-selection-pre-migration.tar.gz

# [ ] 确认维护窗口
echo "迁移时间窗口：2024-03-30 22:00 - 2024-03-31 06:00"

# [ ] 通知相关人员
echo "系统维护通知：2024-03-30 22:00 开始系统升级"
```

### 2.2 资源要求

| 资源 | 最小需求 | 推荐需求 |
|------|----------|----------|
| CPU | 4核 | 8核 |
| 内存 | 8GB | 16GB |
| 磁盘 | 50GB可用 | 100GB可用 |
| 网络 | 100Mbps | 1Gbps |
| 时间 | 4小时 | 8小时 |

### 2.3 风险评估

**高风险项目**：
- NAV历史数据回填（4-8小时）
- 数据库迁移可能失败
- 新算法可能产生意外结果

**缓解措施**：
- 在staging环境充分测试
- 分批次进行数据回填
- 准备完整的回滚计划
- 监控关键指标

## 3. 迁移步骤

### 3.1 第1步：部署新代码

```bash
# 1. 切换到维护模式
sudo systemctl stop fund-selection
echo "系统已停止，开始部署新代码"

# 2. 备份当前代码
cp -r /opt/fund-selection /opt/fund-selection.backup

# 3. 拉取最新代码
cd /opt/fund-selection
git pull origin main

# 4. 更新Python依赖
cd backend
source venv/bin/activate
pip install --upgrade pip
pip install -e .

# 5. 验证代码安装
python -c "import app; print('Backend import successful')"

# 6. 更新前端
cd ../frontend
npm install
npm run build

# 7. 验证前端构建
ls -la dist/

# 8. 部署新代码
sudo systemctl start fund-selection
echo "新代码部署完成"

# 9. 验证服务状态
sudo systemctl status fund-selection
curl http://localhost:8000/health
```

### 3.2 第2步：数据库迁移

```bash
# 1. 运行数据库迁移
cd /opt/fund-selection/backend
source venv/bin/activate
python -m app.database.migrate migrate upgrade

# 2. 检查迁移状态
python -m app.database.migrate status

# 3. 验证数据库结构
mysql -u fund_user -p fund_selection -e "
SHOW TABLES;
DESCRIBE factors;
DESCRIBE factor_metrics;
DESCRIBE policy_metrics;
DESCRIBE benchmarks;
"

# 4. 迁移现有数据
python -m scripts.migrate_legacy_data

# 5. 验证迁移结果
mysql -u fund_user -p fund_selection -e "
SELECT COUNT(*) as funds_count FROM funds;
SELECT COUNT(*) as factors_count FROM factors;
SELECT COUNT(*) as benchmarks_count FROM benchmarks;
SELECT COUNT(*) as policy_count FROM policy_metrics;
"

# 6. 检查数据完整性
python -m scripts.validate_migration_data
```

### 3.3 第3步：NAV历史数据回填

```bash
# 1. 启动NAV回填脚本
cd /opt/fund-selection/backend
source venv/bin/activate

# 2. 开始批量回填（耗时4-8小时）
nohup python -m scripts.backfill_nav_history > /var/log/fund-selection/backfill-nav.log 2>&1 &
BACKFILL_PID=$!

# 3. 监控回填进度
echo "NAV回填进程ID: $BACKFILL_PID"

# 4. 定期检查进度
while ps -p $BACKFILL_PID > /dev/null; do
    echo "回填进行中... $(date)"
    mysql -u fund_user -p fund_selection -e "
    SELECT
        COUNT(*) as processed_count,
        COUNT(CASE WHEN nav_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR) THEN 1 END) as recent_count
    FROM nav_history;
    "
    sleep 300  # 每5分钟检查一次
done

# 5. 检查回填结果
echo "NAV回填完成"
tail -20 /var/log/fund-selection/backfill-nav.log

# 6. 验证数据质量
python -m scripts.validate_nav_data
```

### 3.4 第4步：基准数据回填

```bash
# 1. 启动基准数据回填
nohup python -m scripts.backfill_benchmarks > /var/log/fund-selection/backfill-benchmarks.log 2>&1 &
BENCHMARK_PID=$!

echo "基准数据回填进程ID: $BENCHMARK_PID"

# 2. 监控进度
while ps -p $BENCHMARK_PID > /dev/null; do
    echo "基准数据回填进行中... $(date)"
    mysql -u fund_user -p fund_selection -e "
    SELECT
        COUNT(*) as benchmarks_loaded,
        COUNT(DISTINCT fund_code) as funds_with_benchmarks
    FROM benchmarks;
    "
    sleep 300
done

# 3. 验证基准数据
mysql -u fund_user -p fund_selection -e "
SELECT
    fund_code,
    benchmark_name,
    information_ratio,
    upside_capture,
    downside_capture
FROM benchmarks
LIMIT 5;
"
```

### 3.5 第5步：政策数据种子化

```bash
# 1. 种子化政策数据
python -m scripts.seed_policy_data

# 2. 验证政策数据
mysql -u fund_user -p fund_selection -e "
SELECT
    policy_id,
    policy_name,
    effective_from,
    created_at
FROM policy_metrics
ORDER BY created_at DESC
LIMIT 10;
"

# 3. 测试政策评分计算
python -m scripts.test_policy_scoring
```

### 3.6 第6步：启用真实因子计算

```bash
# 1. 更新环境变量
echo "USE_REAL_FACTORS=true" > /etc/fund-selection/.env

# 2. 重启服务
sudo systemctl restart fund-selection

# 3. 验证服务状态
sudo systemctl status fund-selection

# 4. 检查因子计算日志
tail -f /var/log/fund-selection/app.log

# 5. 验证API响应
curl "http://localhost:8000/api/v1/funds/110011" | jq '.data.factors'
```

### 3.7 第7步：验证结果

```bash
# 1. 运行验证脚本
python -m scripts.validate_factors

# 2. 对比新旧评分差异
python -m scripts.compare_scores

# 3. 检查因子计算质量
python -m scripts.validate_factor_quality

# 4. 性能测试
python -m scripts.performance_test

# 5. 数据一致性检查
python -m scripts.data_consistency_check
```

## 4. 回滚计划

### 4.1 快速回滚

如果迁移过程中出现严重问题，可以快速回滚：

```bash
# 1. 停止新服务
sudo systemctl stop fund-selection

# 2. 回滚代码
sudo rm -rf /opt/fund-selection/backend
sudo cp -r /opt/fund-selection.backup /opt/fund-selection

# 3. 恢复环境变量
cp /opt/fund-selection.backup/.env /etc/fund-selection/.env

# 4. 启动旧服务
sudo systemctl start fund-selection

# 5. 验证服务状态
sudo systemctl status fund-selection
curl http://localhost:8000/health
```

### 4.2 数据库回滚

如果数据库迁移失败：

```bash
# 1. 恢复数据库备份
mysql -u root -p fund_selection < /backup/fund-selection-pre-migration.sql

# 2. 重置环境变量
echo "USE_REAL_FACTORS=false" > /etc/fund-selection/.env

# 3. 重启服务
sudo systemctl restart fund-selection

# 4. 验证数据
mysql -u fund_user -p fund_selection -e "SELECT COUNT(*) FROM funds;"
```

### 4.3 分阶段回滚

如果部分功能有问题，可以选择性回滚：

```bash
# 1. 回滚特定模块
cd /opt/fund-selection/backend
git checkout main -- app/factors/
pip install -e .

# 2. 回滚到旧算法
echo "USE_REAL_FACTORS=false" > /etc/fund-selection/.env
sudo systemctl restart fund-selection

# 3. 保持其他功能升级
echo "系统已部分回滚，但其他功能仍保持升级状态"
```

## 5. 迁移后任务

### 5.1 监控和验证

```bash
# 1. 持续监控系统状态
watch -n 60 "curl http://localhost:8000/health && echo 'API正常'"

# 2. 监控数据库性能
mysql -u fund_user -p fund_selection -e "
SHOW PROCESSLIST;
SHOW STATUS LIKE 'Threads%';
SHOW STATUS LIKE 'Connections%';
"

# 3. 检查错误日志
tail -f /var/log/fund-selection/app.log

# 4. 验证因子计算
mysql -u fund_user -p fund_selection -e "
SELECT
    COUNT(*) as total_funds,
    AVG(final_score) as avg_score,
    MIN(final_score) as min_score,
    MAX(final_score) as max_score
FROM fund_scores;
"
```

### 5.2 性能优化

```bash
# 1. 检查数据库性能
mysql -u fund_user -p fund_selection -e "
SHOW FULL PROCESSLIST;
SELECT * FROM information_schema.PROCESSLIST
WHERE COMMAND != 'Sleep';
"

# 2. 添加数据库索引
mysql -u fund_user -p fund_selection -e "
CREATE INDEX idx_funds_updated_at ON funds(updated_at);
CREATE INDEX idx_factors_fund_code ON factors(fund_code);
CREATE INDEX idx_benchmarks_fund_code ON benchmarks(fund_code);
"

# 3. 优化查询
mysql -u fund_user -p fund_selection -e "
EXPLAIN SELECT f.*, fm.*
FROM funds f
JOIN factor_metrics fm ON f.code = fm.fund_code
WHERE f.category = '股票型'
LIMIT 10;
"
```

### 5.3 数据清理

```bash
# 1. 清理临时数据
mysql -u fund_user -p fund_selection -e "
DELETE FROM temp_migration_logs WHERE created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
"

# 2. 归档旧数据
mysql -u fund_user -p fund_selection -e "
CREATE TABLE factor_metrics_archive AS
SELECT * FROM factor_metrics
WHERE updated_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
"

# 3. 优化表空间
mysql -u fund_user -p fund_selection -e "
OPTIMIZE TABLE funds, factors, factor_metrics, benchmarks;
"
```

## 6. 常见问题

### 6.1 数据迁移问题

**问题**：数据库迁移失败
```bash
# 错误示例：Table 'funds' already exists
mysql -u fund_user -p fund_selection -e "SHOW TABLES;"
```

**解决方案**：
```bash
# 1. 检查现有表结构
mysql -u fund_user -p fund_selection -e "DESCRIBE funds;"

# 2. 清理冲突表
mysql -u fund_user -p fund_selection -e "DROP TABLE IF EXISTS factor_metrics;"

# 3. 重新运行迁移
python -m app.database.migrate migrate upgrade
```

**问题**：数据完整性验证失败
```bash
# 错误示例：Fund count mismatch
python -m scripts.validate_migration_data
```

**解决方案**：
```bash
# 1. 检查数据差异
mysql -u fund_user -p fund_selection -e "
SELECT
    (SELECT COUNT(*) FROM funds_old) as old_count,
    (SELECT COUNT(*) FROM funds_new) as new_count;
"

# 2. 重新迁移数据
python -m scripts.migrate_legacy_data

# 3. 验证迁移结果
python -m scripts.validate_migration_data
```

### 6.2 算法问题

**问题**：因子计算结果异常
```bash
# 错误示例：负因子值
curl "http://localhost:8000/api/v1/funds/110011" | jq '.data.factors.returns'
```

**解决方案**：
```bash
# 1. 检查计算日志
tail -f /var/log/fund-selection/_factors.log

# 2. 验证输入数据
mysql -u fund_user -p fund_selection -e "
SELECT * FROM nav_history
WHERE fund_code = '110011'
ORDER BY nav_date DESC
LIMIT 5;
"

# 3. 重新计算因子
python -m scripts.recalculate_factors 110011
```

**问题**：评分差异过大
```bash
# 错误示例：评分差异超过20%
python -m scripts.compare_scores
```

**解决方案**：
```bash
# 1. 分析差异原因
python -m scripts.analyze_score_differences

# 2. 调整算法参数
echo "FACTOR_WEIGHTS=0.3,0.3,0.4" > /etc/fund-selection/.env

# 3. 重新计算评分
python -m scripts.recalculate_all_scores
```

### 6.3 性能问题

**问题**：API响应缓慢
```bash
# 错误示例：响应时间超过2秒
curl -w "Time: %{time_total}s\n" -o /dev/null -s "http://localhost:8000/api/v1/funds"
```

**解决方案**：
```bash
# 1. 检查数据库查询性能
mysql -u fund_user -p fund_selection -e "
EXPLAIN SELECT f.* FROM funds f
JOIN factor_metrics fm ON f.code = fm.fund_code
WHERE f.category = '股票型';
"

# 2. 添加数据库索引
mysql -u fund_user -p fund_selection -e "
CREATE INDEX idx_funds_category ON funds(category);
CREATE INDEX idx_factor_metrics_fund_code ON factor_metrics(fund_code);
"

# 3. 优化API缓存
echo "CACHE_TTL_SECONDS=3600" > /etc/fund-selection/.env
sudo systemctl restart fund-selection
```

**问题**：内存使用过高
```bash
# 错误示例：内存使用超过80%
free -h
```

**解决方案**：
```bash
# 1. 检查进程内存
ps aux | grep fund-selection

# 2. 优化Python内存使用
export PYTHONMALLOC=malloc

# 3. 重启服务
sudo systemctl restart fund-selection

# 4. 监控内存使用
watch -n 5 'free -h'
```

### 6.4 连接问题

**问题**：数据库连接失败
```bash
# 错误示例：Can't connect to MySQL server
mysql -u fund_user -p fund_selection -e "SELECT 1;"
```

**解决方案**：
```bash
# 1. 检查MySQL服务状态
sudo systemctl status mysql

# 2. 检查数据库连接
mysql -u root -p -e "SELECT Host, User FROM mysql.user WHERE User = 'fund_user';"

# 3. 检查网络连接
netstat -tulpn | grep :3306

# 4. 重新配置连接
echo "MYSQL_HOST=localhost" > /etc/fund-selection/.env
sudo systemctl restart fund-selection
```

## 7. 最佳实践

### 7.1 迁移策略

**分阶段迁移**：
```bash
# 阶段1：在staging环境测试
./scripts/staging-migration.sh

# 阶段2：生产环境小范围测试
./scripts/pilot-migration.sh --funds-list "110011,210008,110022"

# 阶段3：全面迁移
./scripts/production-migration.sh

# 阶段4：验证和监控
./scripts/verification.sh
```

**并行处理**：
```bash
# 并行处理不同批次
nohup python -m scripts.batch_migrate --batch 1 --total 10 > batch1.log 2>&1 &
nohup python -m scripts.batch_migrate --batch 2 --total 10 > batch2.log 2>&1 &
```

### 7.2 监控和告警

**实时监控脚本**：
```python
#!/usr/bin/env python3
import time
import requests
import mysql.connector
from datetime import datetime, timedelta

def monitor_api_health():
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code != 200:
            raise Exception(f"API health check failed: {response.status_code}")
    except Exception as e:
        send_alert(f"API Health Check Failed: {e}")

def monitor_database():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='fund_user',
            password='your_password',
            database='fund_selection'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
    except Exception as e:
        send_alert(f"Database Connection Failed: {e}")

def monitor_factor_calculation():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='fund_user',
            password='your_password',
            database='fund_selection'
        )
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM factor_metrics
            WHERE updated_at < DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """)
        recent_updates = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        if recent_updates == 0:
            send_alert("No recent factor calculations detected")
    except Exception as e:
        send_alert(f"Factor Monitoring Failed: {e}")

def send_alert(message):
    print(f"ALERT: {message}")
    # 这里可以集成告警系统，如邮件、Slack等

if __name__ == "__main__":
    while True:
        monitor_api_health()
        monitor_database()
        monitor_factor_calculation()
        time.sleep(60)
```

### 7.3 文档记录

**迁移记录模板**：
```markdown
# 迁移操作记录

## 时间
- 开始时间：2024-03-30 22:00
- 结束时间：2024-03-31 02:30
- 总耗时：4.5小时

## 执行人员
- 主操作：[负责人]
- 监控：[监控人员]
- 备控：[备用人员]

## 操作步骤
1. 代码部署：✅ 成功
2. 数据库迁移：✅ 成功
3. NAV回填：✅ 成功（6小时）
4. 基准数据回填：✅ 成功（2小时）
5. 政策数据种子化：✅ 成功
6. 启用真实因子：✅ 成功

## 验证结果
- API健康检查：✅ 通过
- 数据完整性：✅ 通过
- 性能测试：✅ 通过
- 评分对比：差异在合理范围内

## 问题记录
- 问题1：数据库连接超时 → 解决方案：增加连接超时时间
- 问题2：因子计算缓慢 → 解决方案：优化计算算法

## 后续任务
- 监控系统状态24小时
- 收集用户反馈
- 性能优化调整
```

### 7.4 测试验证

**验证脚本集合**：
```bash
#!/bin/bash
# migration-verification.sh

echo "开始迁移验证..."

# 1. 健康检查
echo "1. 检查API健康状态..."
if curl -f http://localhost:8000/health; then
    echo "✅ API健康检查通过"
else
    echo "❌ API健康检查失败"
    exit 1
fi

# 2. 数据完整性检查
echo "2. 检查数据完整性..."
python -m scripts.validate_migration_data
if [ $? -eq 0 ]; then
    echo "✅ 数据完整性检查通过"
else
    echo "❌ 数据完整性检查失败"
    exit 1
fi

# 3. 因子质量检查
echo "3. 检查因子计算质量..."
python -m scripts.validate_factor_quality
if [ $? -eq 0 ]; then
    echo "✅ 因子质量检查通过"
else
    echo "❌ 因子质量检查失败"
    exit 1
fi

# 4. 性能测试
echo "4. 运行性能测试..."
python -m scripts.performance_test
if [ $? -eq 0 ]; then
    echo "✅ 性能测试通过"
else
    echo "❌ 性能测试失败"
    exit 1
fi

# 5. 兼容性测试
echo "5. 检查API兼容性..."
curl -f "http://localhost:8000/api/v1/funds" > /dev/null
curl -f "http://localhost:8000/api/v1/funds/110011" > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ API兼容性检查通过"
else
    echo "❌ API兼容性检查失败"
    exit 1
fi

echo "所有验证检查通过！"
```

## 8. 迁移后支持

### 8.1 24小时监控

```bash
# 设置监控服务
cat > /etc/systemd/system/fund-selection-migration-monitor.service << EOF
[Unit]
Description=Fund Selection Migration Monitor
After=network.target

[Service]
Type=simple
User=fund-user
WorkingDirectory=/opt/fund-selection/backend
ExecStart=/opt/fund-selection/backend/venv/bin/python /opt/fund-selection/scripts/migration_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启动监控
sudo systemctl daemon-reload
sudo systemctl enable fund-selection-migration-monitor
sudo systemctl start fund-selection-migration-monitor
```

### 8.2 应急响应

**应急联系人**：
- 技术负责人：tech-leader@fund-selection.com
- 运维工程师：ops@fund-selection.com
- 系统管理员：admin@fund-selection.com

**应急流程**：
1. 问题识别 → 15分钟内上报
2. 问题评估 → 30分钟内确定影响范围
3. 应急处理 → 1小时内开始解决
4. 问题解决 → 4小时内恢复服务
5. 事后总结 → 24小时内提交报告

### 8.3 支持文档

**在线支持**：
- 迁移文档：[https://docs.fund-selection.com/migration](https://docs.fund-selection.com/migration)
- 常见问题：[https://docs.fund-selection.com/faq/migration](https://docs.fund-selection.com/faq/migration)
- 视频教程：[https://video.fund-selection.com/migration](https://video.fund-selection.com/migration)

**离线文档**：
- 迁移手册：/docs/MIGRATION.md
- 操作指南：/docs/OPERATION.md
- 故障排除：/docs/TROUBLESHOOTING.md

## 9. 总结

本迁移指南提供了从遗留系统到生产系统的完整迁移流程，包括：

✅ **充分准备**：环境检查、风险评估、资源准备
✅ **详细步骤**：7个主要迁移步骤，每个步骤都有具体的执行命令
✅ **回滚计划**：快速回滚、数据库回滚、分阶段回滚
✅ **问题解决**：常见问题的详细解决方案
✅ **最佳实践**：分阶段迁移、实时监控、文档记录
✅ **后续支持**：24小时监控、应急响应、支持文档

按照本指南操作，可以确保基金选择系统从MD5哈希系统平滑过渡到基于真实金融数学模型的生产级评分系统，为用户提供更准确、更可靠的基金评估服务。