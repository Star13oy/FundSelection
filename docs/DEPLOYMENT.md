# 生产部署指南

目标受众：DevOps工程师和系统管理员

## 1. 系统要求

### 1.1 硬件要求

| 组件 | 最低配置 | 推荐配置 | 描述 |
|------|----------|----------|------|
| CPU | 4核 | 8核 | 现代CPU支持并发处理 |
| RAM | 8GB | 16GB | 确保数据处理性能 |
| 磁盘 | 100GB SSD | 200GB SSD | 高速存储支持数据库 |
| 网络 | 100Mbps | 1Gbps | 快速数据同步 |

### 1.2 操作系统

- **首选**：Ubuntu 22.04 LTS
- **备选**：
  - CentOS 8/RHEL 8
  - Debian 11
  - Windows Server 2019+（不推荐）

### 1.3 软件依赖

| 软件 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 运行后端服务 |
| Node.js | 18+ | 运行前端构建 |
| MySQL | 8.0+ | 主数据库 |
| Nginx | 1.20+ | 反向代理 |
| Docker | 20.10+ | 容器化部署（可选） |
| Certbot | 1.20+ | SSL证书管理 |

## 2. 环境配置

### 2.1 生产环境变量

创建 `/etc/fund-selection/.env` 文件：

```bash
# 数据库配置
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=fund_user
MYSQL_PASSWORD=your_secure_password_here
MYSQL_DATABASE=fund_selection
MYSQL_CHARSET=utf8mb4

# 功能开关
USE_REAL_FACTORS=true
AKSHARE_ENABLED=true
MARKET_UPDATE_INTERVAL_MINUTES=30

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/var/log/fund-selection/app.log
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=5

# 性能配置
MAX_WORKERS=5
BATCH_SIZE=1000
CACHE_TTL_SECONDS=3600

# 安全配置
CORS_ORIGINS=["https://your-domain.com"]
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# 监控配置
SENTRY_DSN=https://your-sentry-dsn
METRICS_ENABLED=true

# 数据源配置
AKSHARE_TIMEOUT=30
AKSHARE_RETRIES=3
BENCHMARK_DATA_SOURCE=akshare
```

### 2.2 数据库配置

#### MySQL 生产配置

创建 MySQL 配置文件 `/etc/mysql/conf.d/fund-selection.cnf`：

```ini
[mysqld]
# 基础配置
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
default-storage-engine = InnoDB
sql-mode = STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION

# 性能配置
innodb_buffer_pool_size = 4G
innodb_log_file_size = 512M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT
innodb_read_io_threads = 8
innodb_write_io_threads = 8

# 连接配置
max_connections = 200
max_allowed_packet = 256M
wait_timeout = 300
interactive_timeout = 300

# 日志配置
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow-query.log
long_query_time = 2
log_queries_not_using_indexes = 1

# 安全配置
skip-name-resolve
bind-address = 127.0.0.1
```

#### 用户权限配置

```sql
-- 创建专用数据库用户
CREATE USER 'fund_user'@'localhost' IDENTIFIED BY 'your_secure_password';
CREATE USER 'fund_user'@'127.0.0.1' IDENTIFIED BY 'your_secure_password';

-- 授予权限
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, DROP, REFERENCES ON fund_selection.* TO 'fund_user'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, DROP, REFERENCES ON fund_selection.* TO 'fund_user'@'127.0.0.1';

-- 刷新权限
FLUSH PRIVILEGES;
```

### 2.3 系统优化

#### 系统限制配置

编辑 `/etc/security/limits.conf`：

```
# Fund Selection Service Limits
fund_user soft nofile 65536
fund_user hard nofile 65536
fund_user soft nproc 4096
fund_user hard nproc 4096
fund_user soft memlock unlimited
fund_user hard memlock unlimited
```

#### 内核参数优化

编辑 `/etc/sysctl.conf`：

```
# Fund Selection System Optimization
vm.swappiness = 10
vm.dirty_ratio = 60
vm.dirty_background_ratio = 2
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 4096
net.core.netdev_max_backlog = 65536
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30
fs.file-max = 65536
```

应用配置：
```bash
sysctl -p
```

## 3. 部署步骤

### 3.1 选项A：Docker 部署（推荐）

#### 3.1.1 构建 Docker 镜像

```bash
# 克隆代码
git clone git@github.com:Star13oy/FundSelection.git
cd FundSelection

# 构建后端镜像
cd backend
docker build -t fund-selection-backend:latest .

# 构建前端镜像
cd ../frontend
docker build -t fund-selection-frontend:latest .

# 构建 Docker Compose
cd ..
cat > docker-compose.yml << EOF
version: '3.8'

services:
  backend:
    image: fund-selection-backend:latest
    restart: unless-stopped
    environment:
      - DB_TYPE=mysql
      - MYSQL_HOST=mysql
      - MYSQL_PORT=3306
      - MYSQL_USER=fund_user
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
      - MYSQL_DATABASE=fund_selection
      - USE_REAL_FACTORS=true
      - AKSHARE_ENABLED=true
      - LOG_LEVEL=INFO
    depends_on:
      - mysql
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - fund-selection-network

  frontend:
    image: fund-selection-frontend:latest
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    networks:
      - fund-selection-network

  mysql:
    image: mysql:8.0
    restart: unless-stopped
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_USER=fund_user
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
      - MYSQL_DATABASE=fund_selection
      - MYSQL_CHARACTER_SET_SERVER=utf8mb4
      - MYSQL_COLLATION_SERVER=utf8mb4_unicode_ci
    volumes:
      - mysql_data:/var/lib/mysql
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - fund-selection-network

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - fund-selection-network

volumes:
  mysql_data:
  redis_data:

networks:
  fund-selection-network:
    driver: bridge
EOF
```

#### 3.1.2 部署 Docker Compose

```bash
# 创建必要的目录
sudo mkdir -p /var/log/fund-selection
sudo mkdir -p /etc/fund-selection
sudo mkdir -p /etc/ssl/fund-selection

# 设置权限
sudo chown -R $USER:$USER /var/log/fund-selection
sudo chown -R $USER:$USER /etc/fund-selection
sudo chown -R $USER:$USER /etc/ssl/fund-selection

# 创建环境变量文件
cat > .env << EOF
MYSQL_ROOT_PASSWORD=your_root_password_here
MYSQL_PASSWORD=your_secure_password_here
DOMAIN=your-domain.com
EOF

# 启动服务
docker-compose up -d

# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

### 3.2 选项B：系统服务部署

#### 3.2.1 创建系统用户

```bash
# 创建专用用户
sudo useradd -m -s /bin/bash fund-user
sudo usermod -aG sudo fund-user
```

#### 3.2.2 部署后端服务

```bash
# 创建应用目录
sudo mkdir -p /opt/fund-selection
sudo chown -R fund-user:fund-user /opt/fund-selection

# 复制代码
sudo cp -r /path/to/FundSelection/backend /opt/fund-selection/
sudo chown -R fund-user:fund-user /opt/fund-selection/backend

# 创建服务配置
cat > /etc/systemd/system/fund-selection.service << EOF
[Unit]
Description=Fund Selection Backend Service
After=network.target mysql.service
Requires=mysql.service

[Service]
Type=exec
User=fund-user
Group=fund-user
WorkingDirectory=/opt/fund-selection/backend
Environment=PYTHONPATH=/opt/fund_selection/backend
ExecStart=/opt/fund-selection/backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# 安全设置
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/opt/fund-selection/backend/logs
ReadWritePaths=/var/log/fund-selection

# 资源限制
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF
```

#### 3.2.3 部署前端服务

```bash
# 创建前端目录
sudo mkdir -p /var/www/fund-selection
sudo chown -R fund-user:fund-user /var/www/fund-selection

# 复制构建后的前端文件
cd /path/to/FundSelection/frontend
npm run build
sudo cp -r dist/* /var/www/fund-selection/
sudo chown -R fund-user:fund-user /var/www/fund-selection

# 创建 Nginx 配置
cat > /etc/nginx/sites-available/fund-selection << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # 重定向到 HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL 配置
    ssl_certificate /etc/ssl/fund-selection/fullchain.pem;
    ssl_certificate_key /etc/ssl/fund-selection/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # 日志配置
    access_log /var/log/nginx/fund-selection.access.log;
    error_log /var/log/nginx/fund-selection.error.log;

    # 前端静态文件
    location / {
        root /var/www/fund-selection;
        try_files \$uri \$uri/ /index.html;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # 超时配置
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;

        # 缓存配置
        proxy_cache_bypass \$http_pragma;
        add_header X-Cache \$upstream_cache_status;
    }

    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }

    # 错误页面
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
EOF
```

#### 3.2.4 启动服务

```bash
# 启动并启用服务
sudo systemctl daemon-reload
sudo systemctl enable fund-selection
sudo systemctl start fund-selection

# 检查服务状态
sudo systemctl status fund-selection

# 启用 Nginx 站点
sudo ln -s /etc/nginx/sites-available/fund-selection /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 4. 数据库初始化

### 4.1 生产环境数据库准备

```bash
# 登录 MySQL
sudo mysql -u root -p

# 创建数据库和用户
CREATE DATABASE fund_selection CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'fund_user'@'localhost' IDENTIFIED BY 'your_secure_password';
CREATE USER 'fund_user'@'127.0.0.1' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON fund_selection.* TO 'fund_user'@'localhost';
GRANT ALL PRIVILEGES ON fund_selection.* TO 'fund_user'@'127.0.0.1';
FLUSH PRIVILEGES;
EXIT;
```

### 4.2 运行数据库迁移

```bash
# 切换到应用目录
cd /opt/fund-selection/backend

# 激活虚拟环境
source venv/bin/activate

# 运行迁移
python -m app.database.migrations migrate upgrade

# 检查迁移状态
python -m app.database.migrations status
```

### 4.3 种子数据填充

```bash
# 填充基础数据
python -m scripts.seed_production_data

# 填充基准数据
python -m scripts.seed_benchmark_data

# 填充政策数据
python -m scripts.seed_policy_data
```

### 4.4 数据库验证

```bash
# 验证数据库连接
python -c "
from app.db import Database
db = Database()
print(f'Connected to {db.db_type}')
print(f'Tables: {db.get_tables()}')
print(f'Fund count: {db.execute(\"SELECT COUNT(*) FROM funds\").fetchone()[0]}')
"

# 验证数据完整性
python -m scripts.validate_data
```

## 5. 反向代理配置

### 5.1 Nginx 配置优化

```nginx
# /etc/nginx/nginx.conf
user www-data;
worker_processes auto;
pid /run/nginx.pid;
events {
    worker_connections 2048;
    multi_accept on;
    use epoll;
}

http {
    # 基础配置
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    # MIME 类型
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 日志格式
    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                    '\$status \$body_bytes_sent "\$http_referer" '
                    '"\$http_user_agent" "\$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # 缓存配置
    open_file_cache max=200000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;

    # 包含站点配置
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
```

### 5.2 SSL 证书配置

```bash
# 安装 Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# 获取 SSL 证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 自动续期
sudo crontab -e
# 添加以下行：
0 12 * * * /usr/bin/certbot renew --quiet
```

## 6. 监控和日志

### 6.1 应用监控配置

```bash
# 创建监控脚本
cat > /opt/fund-selection/backend/monitor.py << EOF
#!/usr/bin/env python3
import requests
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_api_health():
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            logger.info("API health check passed")
            return True
        else:
            logger.error(f"API health check failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"API health check error: {e}")
        return False

def check_database():
    try:
        from app.db import Database
        db = Database()
        if db.is_connected():
            logger.info("Database connection check passed")
            return True
        else:
            logger.error("Database connection check failed")
            return False
    except Exception as e:
        logger.error(f"Database health check error: {e}")
        return False

def main():
    while True:
        logger.info(f"Health check at {datetime.now()}")

        api_ok = check_api_health()
        db_ok = check_database()

        if not api_ok or not db_ok:
            logger.error("Health check failed - sending alert")
            # 这里可以集成告警系统

        time.sleep(60)

if __name__ == "__main__":
    main()
EOF
```

### 6.2 日志轮转配置

```bash
# /etc/logrotate.d/fund-selection
/var/log/fund-selection/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 fund-user fund-user
    postrotate
        systemctl reload fund-selection
    endscript
}
```

### 6.3 系统监控

```bash
# 创建监控服务
cat > /etc/systemd/system/fund-selection-monitor.service << EOF
[Unit]
Description=Fund Selection Monitor Service
After=fund-selection.service

[Service]
Type=simple
User=fund-user
Group=fund-user
WorkingDirectory=/opt/fund-selection/backend
ExecStart=/opt/fund-selection/backend/venv/bin/python monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

```bash
# 启动监控服务
sudo systemctl daemon-reload
sudo systemctl enable fund-selection-monitor
sudo systemctl start fund-selection-monitor
```

## 7. 备份策略

### 7.1 数据库备份

```bash
# 创建备份脚本
cat > /opt/fund-selection/scripts/backup.sh << EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/fund-selection"
LOG_FILE="/var/log/fund-selection/backup.log"

# 创建备份目录
mkdir -p \$BACKUP_DIR

# 备份数据库
if [ "\$DB_TYPE" = "mysql" ]; then
    mysqldump -u \$MYSQL_USER -p\$MYSQL_PASSWORD \$MYSQL_DATABASE \
        --single-transaction \
        --routines \
        --triggers \
        --events \
        --hex-blob \
        > \$BACKUP_DIR/fund_selection_\$DATE.sql

    # 压缩备份
    gzip \$BACKUP_DIR/fund_selection_\$DATE.sql

    # 删除30天前的备份
    find \$BACKUP_DIR -name "*.gz" -mtime +30 -delete
fi

# 备份配置文件
cp /etc/fund-selection/.env \$BACKUP_DIR/config_\$DATE.env
gzip \$BACKUP_DIR/config_\$DATE.env

# 记录日志
echo "Backup completed at \$(date)" >> \$LOG_FILE
echo "Database backup: \$BACKUP_DIR/fund_selection_\$DATE.sql.gz" >> \$LOG_FILE
echo "Config backup: \$BACKUP_DIR/config_\$DATE.env.gz" >> \$LOG_FILE
EOF
```

```bash
# 设置权限
chmod +x /opt/fund-selection/scripts/backup.sh

# 添加到 crontab
crontab -e
# 添加以下行（每天凌晨2点备份）：
0 2 * * * /opt/fund-selection/scripts/backup.sh
```

### 7.2 应用备份

```bash
# 创建应用备份脚本
cat > /opt/fund-selection/scripts/backup_app.sh << EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/fund-selection"
APP_DIR="/opt/fund-selection"

# 备份应用代码
cd /opt/fund-selection
tar -czf \$BACKUP_DIR/fund_selection_app_\$DATE.tar.gz \
    backend \
    frontend \
    scripts \
    --exclude=backend/venv \
    --exclude=frontend/node_modules \
    --exclude=frontend/dist \
    --exclude=backend/*.db

# 删除30天前的备份
find \$BACKUP_DIR -name "fund_selection_app_*.tar.gz" -mtime +30 -delete
EOF
```

```bash
# 设置权限
chmod +x /opt/fund-selection/scripts/backup_app.sh

# 每周备份应用
crontab -e
# 添加以下行：
0 3 * * 0 /opt/fund-selection/scripts/backup_app.sh
```

### 7.3 恢复流程

```bash
# 数据库恢复
gunzip < /var/backups/fund-selection/fund_selection_20240330_020000.sql.gz | mysql -u fund_user -p fund_selection

# 应用恢复
tar -xzf /var/backups/fund-selection/fund_selection_app_20240330_030000.tar.gz -C /opt/fund-selection

# 重新启动服务
sudo systemctl restart fund-selection
```

## 8. 故障排除

### 8.1 常见问题

#### 服务无法启动

```bash
# 检查服务状态
sudo systemctl status fund-selection

# 查看错误日志
sudo journalctl -u fund-selection -f

# 检查端口占用
sudo netstat -tulpn | grep :8000

# 检查依赖服务
sudo systemctl status mysql nginx
```

#### 数据库连接问题

```bash
# 检查数据库连接
mysql -u fund_user -p fund_selection

# 检查数据库配置
sudo systemctl status mysql
sudo journalctl -u mysql

# 检查数据库权限
mysql -u root -p -e "SELECT User, Host FROM mysql.user WHERE User = 'fund_user';"
```

#### 内存不足

```bash
# 检查内存使用
free -h
htop

# 优化 MySQL 内存
sudo systemctl restart mysql
```

#### 磁盘空间不足

```bash
# 检查磁盘使用
df -h
du -sh /var/log/fund-selection
du -sh /var/backups/fund-selection

# 清理日志
sudo logrotate -f /etc/logrotate.d/fund-selection

# 清理备份
find /var/backups/fund-selection -name "*.gz" -mtime +60 -delete
```

### 8.2 性能调优

#### 应用性能优化

```bash
# 检查应用性能
python -m cProfile -o profile_output.py app.main.py

# 优化 Python 性能
export PYTHONOPTIMIZE=1

# 使用更快的 Python 实现
sudo apt install python3.11-dev
```

#### 数据库性能优化

```sql
-- 检查慢查询
SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;

-- 优化查询
EXPLAIN SELECT * FROM funds WHERE category = '股票型';

-- 添加索引
CREATE INDEX idx_category ON funds(category);
CREATE INDEX idx_risk_level ON funds(risk_level);
CREATE INDEX idx_updated_at ON funds(updated_at);
```

#### Nginx 性能优化

```nginx
# 优化 Nginx 配置
worker_processes auto;
worker_rlimit_nofile 100000;

events {
    worker_connections 4096;
    multi_accept on;
}

http {
    # 开启缓存
    open_file_cache max=200000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;
}
```

### 8.3 安全加固

#### 防火墙配置

```bash
# 安装 UFW
sudo apt install ufw

# 配置防火墙规则
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable

# 检查状态
sudo ufw status
```

#### 应用安全

```bash
# 更新依赖
pip install --upgrade -r requirements.txt

# 安全扫描
pip install safety
safety check

# 依赖检查
pip install pip-check
pip-check
```

#### 数据库安全

```sql
-- 删除默认用户
DROP USER IF EXISTS ''@'localhost';
DROP USER IF EXISTS ''@'127.0.0.1';

-- 限制用户权限
REVOKE ALL PRIVILEGES ON *.* FROM 'fund_user'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX ON fund_selection.* TO 'fund_user'@'localhost';

-- 启用 SSL
ALTER USER 'fund_user'@'localhost' REQUIRE SSL;
```

## 9. 扩展和维护

### 9.1 版本升级

```bash
# 停止服务
sudo systemctl stop fund-selection

# 备份当前版本
sudo systemctl stop fund-selection
sudo cp -r /opt/fund-selection /opt/fund-selection.backup

# 更新代码
git pull origin main

# 更新依赖
cd /opt/fund-selection/backend
source venv/bin/activate
pip install -e .

# 重新部署
sudo systemctl start fund-selection

# 检查服务状态
sudo systemctl status fund-selection
```

### 9.2 水平扩展

#### 负载均衡配置

```nginx
# /etc/nginx/conf.d/load-balancer.conf
upstream backend {
    least_conn;
    server 127.0.0.1:8000 weight=3;
    server 127.0.0.1:8001 weight=3;
    server 127.0.0.1:8002 weight=3;
}

server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

#### 容器化扩展

```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  backend:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 9.3 监控和告警

#### 集成 Prometheus

```python
# 监控指标
import prometheus_client

# 创建指标
REQUEST_COUNT = prometheus_client.Counter(
    'api_requests_total',
    'Total API requests'
)
REQUEST_DURATION = prometheus_client.Histogram(
    'api_request_duration_seconds',
    'API request duration'
)
ERROR_COUNT = prometheus_client.Counter(
    'api_errors_total',
    'Total API errors'
)

# 在中间件中收集指标
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)

    REQUEST_COUNT.inc()
    REQUEST_DURATION.observe(time.time() - start_time)

    if response.status_code >= 400:
        ERROR_COUNT.inc()

    return response
```

#### 集成 Grafana

```json
{
  "dashboard": {
    "title": "Fund Selection Metrics",
    "panels": [
      {
        "title": "API Request Rate",
        "type": "graph",
        "targets": [{
          "expr": "rate(api_requests_total[5m])"
        }]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [{
          "expr": "rate(api_errors_total[5m])"
        }]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m]))"
        }]
      }
    ]
  }
}
```

## 10. 相关文档

### 10.1 参考资料

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Nginx 文档](https://nginx.org/en/docs/)
- [MySQL 文档](https://dev.mysql.com/doc/)
- [Docker 文档](https://docs.docker.com/)
- [Prometheus 文档](https://prometheus.io/docs/)
- [Grafana 文档](https://grafana.com/docs/)

### 10.2 社区支持

- GitHub Issues：[https://github.com/Star13oy/FundSelection/issues](https://github.com/Star13oy/FundSelection/issues)
- 官方文档：[https://docs.fund-selection.com](https://docs.fund-selection.com)
- 技术支持：support@fund-selection.com
- 紧急联系：emergency@fund-selection.com

### 10.3 更新日志

#### v1.0.0 (2024-03-30)
- 初始版本发布
- 支持 Docker 和系统服务两种部署方式
- 集成 MySQL 数据库
- 提供完整的监控和日志系统
- 实现自动化备份和恢复机制

## 11. 总结

本部署指南提供了从零开始部署生产环境的完整流程，包括：

- ✅ 系统要求和配置
- ✅ Docker 和系统服务两种部署方式
- ✅ 数据库初始化和优化
- ✅ 反向代理和 SSL 配置
- ✅ 监控、日志和备份策略
- ✅ 故障排除和安全加固
- ✅ 扩展和维护指南

按照本指南操作，可以确保基金选择系统在生产环境中稳定运行，并为未来的扩展和维护提供良好的基础。