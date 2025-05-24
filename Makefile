.PHONY: help install install-dev test lint format clean run docker-build docker-run

# 默认目标
help:
	@echo "Git2MD - GitHub仓库内容聚合导出工具"
	@echo ""
	@echo "可用命令:"
	@echo "  make install      - 安装生产依赖"
	@echo "  make install-dev  - 安装开发依赖"
	@echo "  make test         - 运行测试"
	@echo "  make lint         - 运行代码检查"
	@echo "  make format       - 格式化代码"
	@echo "  make clean        - 清理临时文件"
	@echo "  make run          - 运行应用"
	@echo "  make docker-build - 构建Docker镜像"
	@echo "  make docker-run   - 运行Docker容器"

# 安装生产依赖
install:
	pip install --upgrade pip
	pip install -r requirements.txt

# 安装开发依赖
install-dev:
	pip install --upgrade pip
	pip install -r requirements-dev.txt
	pre-commit install

# 运行测试
test:
	pytest -v --cov=utils --cov=app --cov-report=term-missing --cov-report=html

# 运行代码检查
lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	mypy . --ignore-missing-imports
	bandit -r . -x /tests

# 格式化代码
format:
	black .
	isort .

# 清理临时文件
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	rm -rf downloads/*
	rm -rf cache/*

# 运行应用
run:
	python app.py

# 构建Docker镜像
docker-build:
	docker build -t git2md:latest .

# 运行Docker容器
docker-run:
	docker run -d -p 5000:5000 --name git2md --env-file .env git2md:latest

# 停止Docker容器
docker-stop:
	docker stop git2md
	docker rm git2md

# 运行所有检查（CI模拟）
ci: lint test
	@echo "所有检查通过！" 