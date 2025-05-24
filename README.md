# GitHub 仓库内容聚合导出工具

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.3%2B-green)](https://flask.palletsprojects.com/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**将GitHub仓库的代码文件聚合导出为单个文件的Web应用**

[功能特性](#-功能特性) •
[快速开始](#-快速开始) •
[使用说明](#-使用说明) •
[部署指南](#-部署指南) •
[API文档](#-api文档)

</div>

## 🚀 功能特性

- **智能聚合**: 将多个代码文件合并为单个文件，便于分享和阅读
- **智能过滤**: 支持文件类型、文件名、目录过滤，内置默认过滤模板
- **TOC目录**: Markdown格式自动生成目录导航
- **Web管理**: 浏览器界面配置GitHub Token和系统设置
- **多种格式**: 支持Markdown和纯文本输出
- **Docker支持**: 完整的容器化部署方案

## 📋 系统要求

- Python 3.8+
- 网络连接（访问GitHub API）
- Docker（可选，用于容器化部署）

## 🚀 快速开始

### 方法1: 本地运行

```bash
# 克隆项目
git clone https://github.com/your-username/git2md.git
cd git2md

# 自动安装并运行
./start.sh          # Linux/macOS
start.bat           # Windows

# 或手动安装
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### 方法2: Docker运行

```bash
# 快速启动
docker run -p 5000:5000 git2md

# 或使用Docker Compose（推荐）
docker-compose up -d
```

### 访问应用

- **主页**: http://localhost:5000
- **管理面板**: http://localhost:5000/admin
- **系统设置**: http://localhost:5000/settings

## 📖 使用说明

### 基本使用

1. **输入仓库URL**: `https://github.com/owner/repo`
2. **配置过滤条件**:
   - 文件类型: `py,js,md`
   - 排除文件: `test_*.py,*.min.js`
   - 排除目录: `tests,docs,node_modules`
   - 默认过滤: 勾选自动过滤常见非源码文件
3. **选择格式**: Markdown（带TOC）或纯文本
4. **导出下载**: 点击开始导出

### GitHub Token配置（推荐）

访问 [GitHub Token设置](https://github.com/settings/tokens) 创建Token:
- 勾选 `public_repo` 权限
- 在 `/settings` 页面配置或设置环境变量 `GITHUB_TOKEN`

**好处**: API限制从60次/小时提升至5000次/小时

### 输出示例

<details>
<summary>Markdown格式（点击展开）</summary>

```markdown
# my-project - 代码聚合文件

生成时间: 2024-05-24 21:30:45
文件数量: 3

## 📑 目录

- [README.md](#readme-md)
- [src/main.py](#src-main-py)

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
```

</details>

## 🐳 部署指南

### Docker Compose部署（推荐）

```bash
# 创建环境文件
cp env.example .env
# 编辑 .env 文件设置配置

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 环境配置

创建 `.env` 文件：

```bash
# GitHub Token（可选但强烈推荐）
GITHUB_TOKEN=your_github_token_here

# 应用配置
SECRET_KEY=your-secret-key
MAX_REPO_SIZE_MB=100
MAX_FILE_COUNT=2000
FILE_RETENTION_MINUTES=30
```

## 🎯 API文档

### POST /download

导出仓库内容

**请求参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| repo_url | string | 是 | GitHub仓库URL |
| file_types | string | 否 | 文件类型，逗号分隔 |
| exclude_names | string | 否 | 排除文件名，支持通配符 |
| exclude_dirs | string | 否 | 排除目录，逗号分隔 |
| output_format | string | 否 | 输出格式: `md`(默认) 或 `txt` |
| use_default_filters | boolean | 否 | 使用默认过滤模板 |

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

### 其他接口

- `GET /health` - 健康检查
- `GET /files/{filename}` - 下载文件
- `POST /settings/token` - 配置GitHub Token

## 🔒 使用限制

- 仅支持公开GitHub仓库
- 仓库大小 ≤ 100MB
- 文件数量 ≤ 2000个
- 单文件大小 ≤ 1MB
- 文件30分钟后自动删除

## 🐛 故障排除

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| API限制错误 | 配置GitHub Token |
| 仓库无法访问 | 确认URL正确且仓库公开 |
| 文件过大/过多 | 使用过滤条件减少文件 |
| Docker权限问题 | 使用 `docker-compose` 或检查目录权限 |

### 获取帮助

- 查看日志: `docker-compose logs -f` 或 `tail -f app.log`
- 提交Issue: [GitHub Issues](https://github.com/your-username/git2md/issues)
- 查看文档: [CONTRIBUTING.md](CONTRIBUTING.md)

## 🤝 贡献

欢迎提交Issue和Pull Request！请查看 [贡献指南](CONTRIBUTING.md)。

## 📄 许可证

[MIT License](LICENSE) © 2024

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/) - Web框架
- [PyGithub](https://github.com/PyGithub/PyGithub) - GitHub API客户端
- [Font Awesome](https://fontawesome.com/) - 图标库
- 该项目的每一行代码都由 Claude 4 书写

---

⭐ **如果这个项目对你有帮助，请给它一个Star！** 