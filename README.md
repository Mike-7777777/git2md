# GitHub 仓库内容聚合导出工具

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-%5E2.3.2-green)](https://flask.palletsprojects.com/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI/CD](https://github.com/your-username/git2md/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/git2md/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/codecov/c/github/your-username/git2md)](https://codecov.io/gh/your-username/git2md)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

</div>

一个强大的Web应用，能够将GitHub仓库的代码文件聚合导出为单个文件，支持多种过滤条件和输出格式。

## 🚀 功能特性

- **智能聚合**: 将多个代码文件合并为一个文件，便于分享和阅读
- **灵活过滤**: 支持按文件类型、文件名模式、目录名过滤
- **默认过滤模板**: 一键过滤常见非源码文件（资源、配置、日志等）
- **多种格式**: 支持Markdown和纯文本两种输出格式
- **智能目录**: Markdown格式自动生成TOC目录，支持快速导航
- **美观界面**: 现代化的响应式Web界面
- **Web端配置**: 可通过浏览器界面配置GitHub Token
- **实时状态**: 处理过程中的实时状态反馈
- **管理面板**: 完整的系统管理和监控功能
- **安全限制**: 内置文件大小、数量等安全限制
- **自动清理**: 临时文件自动清理机制
- **Docker支持**: 完整的容器化部署方案

## 📋 系统要求

- Python 3.8+
- pip 包管理器
- 网络连接（访问GitHub API）
- Docker（可选，用于容器化部署）

## 🛠 快速开始

### 方法1: 本地安装

#### 1. 克隆项目

```bash
git clone https://github.com/your-username/git2md.git
cd git2md
```

#### 2. 自动安装（推荐）

**Linux/macOS:**
```bash
chmod +x start.sh
./start.sh
```

**Windows:**
```cmd
start.bat
```

#### 3. 手动安装

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行应用
python app.py
```

### 方法2: Docker 部署

#### 使用 Docker

```bash
# 构建镜像
docker build -t git2md .

# 运行容器（基础版本）
docker run -p 5000:5000 git2md

# 运行容器（挂载数据目录，推荐）
mkdir -p downloads logs cache
docker run -p 5000:5000 \
  -v $(pwd)/downloads:/app/downloads \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/cache:/app/cache \
  --env-file .env \
  git2md
```

#### 使用 Docker Compose（推荐）

```bash
# 创建必要目录
mkdir -p downloads logs cache

# 复制环境变量文件
cp env.example .env
# 编辑 .env 文件，设置你的GitHub Token

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 3. 访问应用

应用将在以下端口启动：
- **主页**: http://localhost:5000
- **管理面板**: http://localhost:5000/admin  
- **系统设置**: http://localhost:5000/settings

## ⚙️ 配置说明

### 环境变量配置

创建`.env`文件（从`env.example`复制）：

```bash
# GitHub API Token (强烈推荐！避免API限制)
GITHUB_TOKEN=your_github_token_here

# 应用密钥 (生产环境必须修改)
SECRET_KEY=your-super-secret-key-change-in-production

# Flask运行环境
FLASK_ENV=production

# API请求优化配置
REQUEST_DELAY=0.5              # 请求间隔（秒）
CACHE_DURATION=300             # 缓存持续时间（秒）
MAX_RETRY_ATTEMPTS=3           # 最大重试次数

# 应用限制配置
MAX_REPO_SIZE_MB=100           # 最大仓库大小（MB）
MAX_FILE_COUNT=2000            # 最大文件数量
MAX_SINGLE_FILE_SIZE_MB=1      # 单文件最大大小（MB）
FILE_RETENTION_MINUTES=30      # 文件保留时间（分钟）

# 日志级别
LOG_LEVEL=INFO
```

### Web端配置（推荐）

访问 http://localhost:5000/settings 进行可视化配置：

1. **GitHub Token配置**：
   - 安全的Token输入界面
   - 实时验证Token有效性
   - API限制状态显示

2. **系统管理**：
   - 缓存清理
   - 下载文件管理
   - 系统状态监控

### GitHub Token 配置 (重要)

为了避免API限制和提高性能，强烈建议配置GitHub Token：

#### 获取Token步骤：
1. 访问 [GitHub Token 设置页面](https://github.com/settings/tokens)
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 设置Token名称和过期时间
4. 勾选 **public_repo** 权限（读取公开仓库）
5. 点击 "Generate token" 并复制生成的Token

#### 配置方法：
- **Web界面**：访问 `/settings` 页面配置（推荐）
- **环境变量**：在`.env`文件中设置`GITHUB_TOKEN`
- **系统环境**：`export GITHUB_TOKEN=your_token`

#### 使用Token的好处：
- API请求限制从**60次/小时**提升至**5000次/小时**
- 避免"恶意行为检测"错误
- 更稳定快速的服务体验
- 支持处理大型仓库

## 🎛️ 管理界面

### 主要功能页面

1. **主页** (`/`)：
   - 仓库内容导出功能
   - 智能过滤选项
   - 默认过滤模板

2. **管理面板** (`/admin`)：
   - GitHub Token状态检查
   - 缓存统计和清理
   - 系统状态监控
   - 健康检查功能

3. **系统设置** (`/settings`)：
   - GitHub Token配置界面
   - API限制实时显示
   - 系统参数管理
   - 文件清理工具

### 默认过滤功能

新增智能默认过滤功能，一键过滤常见非源码内容：

- **排除目录**（26个）：assets, images, dist, build, node_modules, .git 等
- **排除文件**（29个）：LICENSE, .gitignore, .env, Docker相关文件等
- **排除扩展名**（55个）：.log, .tmp, 图片文件, 视频文件, 编译产物等

## 📖 使用说明

### 基本使用

1. **输入仓库URL**: 输入完整的GitHub仓库地址
   ```
   https://github.com/owner/repo
   ```

2. **设置过滤条件**（可选）:
   - **默认过滤模板**: 勾选可自动过滤常见非源码文件
   - **文件类型**: 如 `py,md,txt` 只包含这些扩展名的文件
   - **排除文件名**: 如 `test_*.py,README.md` 排除匹配的文件
   - **排除目录**: 如 `tests,docs` 排除这些目录

3. **选择输出格式**:
   - **Markdown**: 带语法高亮的格式化输出，自动生成TOC目录
   - **纯文本**: 简单的文本格式

4. **开始导出**: 点击"开始导出"按钮

### TOC目录功能

当选择Markdown格式时，系统会自动生成以下内容：

1. **自动目录生成**: 
   - 基于文件路径自动生成目录链接
   - 按文件路径字母排序
   - 支持点击跳转到对应文件

2. **导航功能**:
   - 每个文件末尾都有"返回目录"链接
   - 使用📄 emoji标识文件
   - 文件路径作为锚点链接

3. **兼容性**:
   - 兼容GitHub、GitLab等Markdown渲染器
   - 支持VS Code、Typora等编辑器
   - 在线Markdown查看器完全支持

### 高级用法

#### 文件类型过滤
```
# 只包含Python和Markdown文件
py,md

# 包含多种代码文件
py,js,html,css,md
```

#### 文件名排除模式
```
# 排除测试文件
test_*.py,*_test.py

# 排除特定文件
README.md,LICENSE,*.min.js
```

#### 目录排除
```
# 排除常见的非源码目录
tests,docs,.github,node_modules
```

### 输出格式示例

#### Markdown格式（包含目录）
```markdown
# my-project - 代码聚合文件

生成时间: 2024-05-24 21:30:45
文件数量: 3

## 📑 目录

- [README.md](#readme-md)
- [src/main.py](#src-main-py)
- [src/utils.py](#src-utils-py)

---

## <a id="readme-md"></a>📄 /README.md

# Project Title
This is a sample project.

[⬆️ 返回目录](#-目录)

## <a id="src-main-py"></a>📄 /src/main.py

```python
def hello_world():
    print("Hello, World!")
```

[⬆️ 返回目录](#-目录)

## <a id="src-utils-py"></a>📄 /src/utils.py

```python
def helper_function():
    return "This is a helper function"
```

[⬆️ 返回目录](#-目录)
```

#### 纯文本格式
```
my-project - 代码聚合文件
生成时间: 2024-05-24 21:30:45
文件数量: 3
================================================================================

===== /README.md =====
# Project Title
This is a sample project.

===== /src/main.py =====
def hello_world():
    print("Hello, World!")

===== /src/utils.py =====
def helper_function():
    return "This is a helper function"
```

## 🔒 使用限制

- 仅支持公开的GitHub仓库
- 仓库大小不超过 100MB
- 文件数量不超过 2000 个
- 单个文件不超过 1MB
- 下载文件30分钟后自动删除
- GitHub API有请求频率限制

## 🎯 API 接口

### POST /download

导出仓库内容

**请求参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| repo_url | string | 是 | GitHub仓库URL |
| file_types | string | 否 | 文件类型，逗号分隔 |
| exclude_names | string | 否 | 排除文件名，逗号分隔，支持通配符 |
| exclude_dirs | string | 否 | 排除目录，逗号分隔 |
| output_format | string | 否 | 输出格式 (md/txt)，md格式包含TOC目录 |
| use_default_filters | boolean | 否 | 是否使用默认过滤模板 |

**响应示例:**

```json
{
  "status": "success",
  "download_url": "/files/repo_merged_20240524.md",
  "file_size": 20789,
  "file_count": 17,
  "processing_time": 3.45,
  "message": "导出成功"
}
```

### GET /files/{filename}

下载生成的文件

### GET /health

健康检查接口

## 🛡️ 安全考虑

- 输入参数严格校验
- 文件大小和数量限制
- 临时文件自动清理
- 不暴露内部错误信息
- 仅支持公开仓库访问

## 🐛 故障排除

### 常见问题

1. **仓库无法访问**
   - 确认仓库URL正确
   - 确认仓库是公开的
   - 检查网络连接

2. **API限制错误**
   - 设置GitHub Token环境变量
   - 稍后重试

3. **文件过大或过多**
   - 使用过滤条件减少文件数量
   - 排除大文件或目录

4. **下载文件不存在**
   - 文件可能已过期自动删除
   - 重新生成文件

### 日志查看

应用日志保存在 `app.log` 文件中：

```bash
tail -f app.log
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/) - Web框架
- [PyGithub](https://github.com/PyGithub/PyGithub) - GitHub API客户端
- [Font Awesome](https://fontawesome.com/) - 图标库

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 [Issue](https://github.com/your-username/git2md/issues)
- 发送邮件至: your-email@example.com

---

⭐ 如果这个项目对你有帮助，请给它一个 Star！ 

### v1.1.0 (2024-05-24)
- ✨ 新增Web端GitHub Token配置功能
- ✨ 新增默认过滤模板（一键过滤常见非源码文件）
- ✨ 新增Markdown格式TOC目录功能，支持快速导航
- ✨ 新增系统设置页面和管理界面优化
- 🐛 修复Docker容器权限问题
- 🐛 修复.env文件加载问题
- 📝 完善文档和部署指南 