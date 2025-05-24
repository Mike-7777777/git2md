# 变更日志

所有重要的变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且该项目遵循 [语义化版本](https://semver.org/lang/zh-CN/spec/v2.0.0.html)。

## [Unreleased]

### 添加
- 准备下一版本的功能

## [1.0.0] - 2024-01-20

### 添加
- 🚀 首次发布
- 核心功能：将GitHub仓库代码文件聚合为单个文件
- 支持Markdown和纯文本两种输出格式
- 智能文件过滤功能
  - 按文件类型过滤
  - 按文件名模式排除
  - 按目录排除
  - 默认过滤模板（排除常见非源码文件）
- GitHub API优化
  - 智能缓存机制（5分钟有效期）
  - 批量文件处理
  - 请求速率限制
  - GitHub Token支持
- 美观的Web界面
  - 响应式设计
  - 实时状态反馈
  - 表单验证
- 管理面板
  - GitHub Token配置状态
  - 缓存管理
  - 系统监控
- 安全特性
  - 输入参数验证
  - 文件大小限制
  - 自动清理机制
- 完善的文档
  - 详细的README
  - API文档
  - 部署指南
  - 贡献指南
- 开发工具
  - 单元测试
  - CI/CD配置
  - pre-commit钩子
  - Docker支持

### 安全
- 防止路径穿越攻击
- 限制仓库大小（100MB）
- 限制文件数量（2000个）
- 限制单文件大小（1MB）

### 已知问题
- 仅支持公开仓库
- 大文件全部加载到内存
- 未实现断点续传

## [0.1.0] - 2024-01-15

### 添加
- 初始原型开发
- 基本的文件聚合功能
- 简单的Web界面

[Unreleased]: https://github.com/your-username/git2md/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/your-username/git2md/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/your-username/git2md/releases/tag/v0.1.0 