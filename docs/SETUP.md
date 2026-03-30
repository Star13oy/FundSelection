# 开发环境设置指南

目标受众：设置系统本地环境的开发人员

## 1. 前置条件

### 必需组件

- **Python 3.11+**：推荐使用 Python 3.12 或更高版本
  - 验证安装：`python --version` 或 `python3 --version`
- **Git**：版本控制工具
  - 验证安装：`git --version`
- **Node.js 18+**：JavaScript 运行时环境
  - 验证安装：`node --version`
- **npm**：Node.js 包管理器
  - 验证安装：`npm --version`

### 可选组件

- **MySQL 8.0+**：生产环境数据库
  - 开发环境可以使用 SQLite 无需额外配置
  - 验证安装：`mysql --version`
- **VS Code**：推荐的编辑器（可选）
  - 安装 Python 扩展、ESLint、Prettier 等插件

## 2. 安装步骤

### 2.1 克隆仓库

```bash
# 克隆仓库
git clone git@github.com:Star13oy/FundSelection.git
cd FundSelection

# 切换到开发分支（如果存在）
git checkout dev
```

### 2.2 安装后端依赖

```bash
# 进入后端目录
cd backend

# 创建并激活虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或者在 Windows 上：
# venv\Scripts\activate

# 安装 Python 依赖
pip install -e .
# 或使用 pipenv（可选）：
# pipenv install --dev
```

### 2.3 安装前端依赖

```bash
# 进入前端目录
cd ../frontend

# 安装依赖
npm install

# 安装开发依赖
npm install --include=dev
```

### 2.4 验证安装

```bash
# 后端验证
cd ../backend
python -c "import app; print('Backend import successful')"

# 前端验证
cd ../frontend
npm run check
```

## 3. 配置

### 3.1 环境变量配置

```bash
# 复制环境变量模板
cd ../backend
cp .env.example .env

# 复制前端环境变量（如果需要）
cd ../frontend
cp .env.example .env
```

### 3.2 编辑环境变量

编辑 `backend/.env` 文件：

```bash
# 数据库配置
DB_TYPE=sqlite  # 开发环境使用 SQLite
# 如果使用 MySQL：
# DB_TYPE=mysql
# MYSQL_HOST=localhost
# MYSQL_PORT=3306
# MYSQL_USER=fund_user
# MYSQL_PASSWORD=your_password
# MYSQL_DATABASE=fund_selection

# 功能开关
USE_REAL_FACTORS=true
AKSHARE_ENABLED=true

# 日志配置
LOG_LEVEL=DEBUG
LOG_FILE=logs/app.log

# 性能配置
MAX_WORKERS=2
BATCH_SIZE=100

# 市场数据更新间隔（分钟）
MARKET_UPDATE_INTERVAL_MINUTES=30
```

### 3.3 数据库配置

#### SQLite（开发环境）
SQLite 会自动创建，无需额外配置。

#### MySQL（生产环境）

```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库和用户
CREATE DATABASE fund_selection CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'fund_user'@'localhost' IDENTIFIED BY 'strong_password_here';
GRANT ALL PRIVILEGES ON fund_selection.* TO 'fund_user'@'localhost';
FLUSH PRIVILEGES;

# 退出 MySQL
exit;
```

## 4. 数据库初始化

### 4.1 运行数据库迁移

```bash
cd backend

# 初始化数据库迁移
python -m app.database.migrations migrate upgrade

# 检查迁移状态
python -m app.database.migrations status
```

### 4.2 种子数据初始化

```bash
# 填充基础数据
python -m scripts.seed_data

# 填充基准数据（可选）
python -m scripts.seed_benchmark_data

# 填充政策数据（可选）
python -m scripts.seed_policy_data
```

### 4.3 验证数据库

```bash
# 检查数据库连接
python -c "
from app.db import Database
db = Database()
print(f'Database type: {db.db_type}')
print(f'Connected: {db.is_connected()}')
"

# 检查数据表
python -c "
from app.db import Database
db = Database()
tables = db.get_tables()
print(f'Tables: {tables}')
"
```

## 5. 验证设置

### 5.1 运行测试

```bash
# 后端测试
cd backend
pytest tests/ -v

# 带覆盖率报告
pytest tests/ --cov=app --cov-report=html

# 前端测试
cd ../frontend
npm test
npm run test:coverage
```

### 5.2 启动开发服务器

```bash
# 终端 1：启动后端
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 终端 2：启动前端
cd ../frontend
npm run dev
```

### 5.3 验证服务

```bash
# 检查后端健康状态
curl http://localhost:8000/health

# 检查 API 端点
curl http://localhost:8000/api/v1/funds?page=1&page_size=5

# 检查前端访问
curl http://localhost:5173 | head -20
```

## 6. 开发工具配置

### 6.1 VS Code 工作区配置

创建 `.vscode/settings.json`：

```json
{
  "python.analysis.extraPaths": [
    "./backend"
  ],
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.testing.pytestEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "eslint.validate": [
    "javascript",
    "typescript",
    "typescriptreact"
  ],
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  }
}
```

### 6.2 VS Code 扩展推荐

```bash
# 安装推荐的 VS Code 扩展
code --install-extension ms-python.python
code --install-extension ms-vscode.vscode-typescript-next
code --install-extension esbenp.prettier-vscode
code --install-extension ms-vscode.vscode-json
code --install-extension bradlc.vscode-tailwindcss
```

### 6.3 Git 钩子配置

```bash
# 安装 pre-commit 钩子
cd backend
pre-commit install

# 运行 pre-commit 检查
pre-commit run --all-files
```

## 7. 常见问题

### 7.1 依赖安装问题

```bash
# 清除 pip 缓存
pip cache purge

# 重新安装依赖
cd backend
pip uninstall -r requirements.txt -y
pip install -e .

# 清除 npm 缓存
npm cache clean --force
cd frontend
rm -rf node_modules
npm install
```

### 7.2 数据库连接问题

```bash
# 检查 SQLite 文件
ls -la backend/fund_selection.db

# 重置数据库
cd backend
rm -f fund_selection.db
python -m app.database.migrations migrate upgrade
python -m scripts.seed_data
```

### 7.3 端口冲突

```bash
# 查找占用端口的进程
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# 杀死进程
taskkill /F /PID <PID>        # Windows
kill -9 <PID>                 # Linux/Mac
```

### 7.4 环境变量问题

```bash
# 检查环境变量
echo $DB_TYPE                  # Linux/Mac
echo %DB_TYPE%                 # Windows

# 查看所有环境变量
env                          # Linux/Mac
set                          # Windows
```

## 8. 性能优化

### 8.1 Python 优化

```bash
# 安装性能分析工具
pip install memory-profiler line-profiler

# 运行性能分析
cd backend
python -m memory_profiler app.main.py

# 使用 line-profiler
python -m line_profiler -v app.main.py
```

### 8.2 前端优化

```bash
# 构建优化版本
cd frontend
npm run build

# 分析包大小
npm install -g bundle-analyzer
npm run analyze
```

## 9. 开发工作流

### 9.1 代码提交

```bash
# 添加文件
git add backend/app/*.py frontend/src/*.ts

# 提交代码
git commit -m "feat: add new fund factor calculation algorithm

- Implement enhanced risk-adjusted returns calculation
- Add benchmark data integration
- Improve factor standardization pipeline

Constraint: Must maintain backward compatibility
Confidence: medium
Scope-risk: narrow"
```

### 9.2 分支策略

```bash
# 创建功能分支
git checkout -b feature/enhanced-factor-calculation

# 创建修复分支
git checkout -b fix/database-migration-issue

# 删除分支
git branch -d feature/enhanced-factor-calculation
```

## 10. 相关链接

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [React 文档](https://react.dev/)
- [TypeScript 文档](https://www.typescriptlang.org/docs/)
- [Tailwind CSS 文档](https://tailwindcss.com/docs)
- [pytest 文档](https://docs.pytest.org/)
- [MySQL 文档](https://dev.mysql.com/doc/)

## 11. 支持信息

如果遇到问题，请检查以下资源：

1. **GitHub Issues**：[https://github.com/Star13oy/FundSelection/issues](https://github.com/Star13oy/FundSelection/issues)
2. **项目文档**：[docs/](docs/)
3. **API 文档**：[docs/API.md](docs/API.md)
4. **部署文档**：[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

提交 Issue 时，请提供以下信息：
- 操作系统版本
- Python 版本
- Node.js 版本
- 详细的错误信息
- 复现步骤