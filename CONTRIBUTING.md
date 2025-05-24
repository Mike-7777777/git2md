# 贡献指南

感谢您对 Git2MD 项目的关注！我们欢迎所有形式的贡献。

## 🚀 如何贡献

### 报告问题

1. 在提交问题之前，请先搜索现有的 [Issues](https://github.com/your-username/git2md/issues)
2. 如果没有找到相关问题，请创建新的 Issue
3. 请提供：
   - 清晰的问题描述
   - 复现步骤
   - 期望行为
   - 实际行为
   - 环境信息（操作系统、Python版本等）

### 提交代码

1. **Fork 项目**
   ```bash
   git clone https://github.com/your-username/git2md.git
   cd git2md
   ```

2. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **设置开发环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   pre-commit install
   ```

4. **编写代码**
   - 遵循 PEP 8 代码规范
   - 添加类型注解
   - 编写文档字符串
   - 保持代码简洁清晰

5. **编写测试**
   - 为新功能编写单元测试
   - 确保测试覆盖率不降低
   - 运行测试：`pytest`

6. **代码质量检查**
   ```bash
   # 运行所有检查
   black .
   isort .
   flake8 .
   mypy .
   pytest
   ```

7. **提交代码**
   ```bash
   git add .
   git commit -m "feat: 添加新功能"
   ```

8. **推送并创建 Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📝 代码规范

### Python 代码风格

- 使用 Black 格式化代码
- 使用 isort 排序导入
- 遵循 PEP 8 规范
- 最大行长度：127 字符

### 提交信息规范

采用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat:` 新功能
- `fix:` 修复问题
- `docs:` 文档更新
- `style:` 代码格式（不影响代码运行的变动）
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建过程或辅助工具的变动

示例：
```
feat: 添加批量下载功能
fix: 修复文件编码问题
docs: 更新API文档
```

### 文档规范

- 所有公共函数和类都需要文档字符串
- 使用 Google 风格的文档字符串
- 保持 README.md 更新

## 🧪 测试要求

- 新功能必须包含测试
- 修复 bug 需要添加测试用例
- 测试覆盖率目标：80%+
- 测试文件命名：`test_模块名.py`

## 🔍 代码审查

所有 Pull Request 都需要经过代码审查：

1. 代码质量
2. 测试完整性
3. 文档完善度
4. 性能影响
5. 安全性考虑

## 📋 Pull Request 模板

创建 PR 时，请包含：

```markdown
## 描述
简要描述这个 PR 的内容

## 改动类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 破坏性变更
- [ ] 文档更新

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 添加了必要的测试
- [ ] 所有测试通过
- [ ] 更新了相关文档

## 相关 Issue
Closes #(issue)
```

## 🤝 行为准则

- 尊重所有贡献者
- 建设性的批评和讨论
- 欢迎新手参与
- 保持专业和友好

## 📞 联系方式

如有问题，可以通过以下方式联系：

- 创建 Issue
- 发送邮件至：your-email@example.com

再次感谢您的贡献！🎉 