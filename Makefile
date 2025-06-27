.PHONY: help install install-dev test test-unit test-integration lint format clean build upload

help:  ## 显示帮助信息
	@echo "可用命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## 安装项目依赖
	pip install -r requirements.txt

install-dev:  ## 安装开发依赖
	pip install -r requirements.txt
	pip install -e ".[dev]"

test:  ## 运行所有测试
	pytest tests/ -v

test-unit:  ## 运行单元测试
	pytest tests/ -v -m "not integration"

test-integration:  ## 运行集成测试
	pytest tests/ -v -m integration

test-coverage:  ## 运行测试并生成覆盖率报告
	pytest tests/ --cov=meetaudio --cov-report=html --cov-report=term

lint:  ## 代码检查
	flake8 meetaudio/ tests/
	mypy meetaudio/

format:  ## 代码格式化
	black meetaudio/ tests/ examples/
	isort meetaudio/ tests/ examples/

clean:  ## 清理临时文件
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:  ## 构建包
	python setup.py sdist bdist_wheel

upload:  ## 上传到PyPI
	twine upload dist/*

demo:  ## 运行基本示例
	python examples/basic_usage.py

demo-advanced:  ## 运行高级功能示例
	python examples/advanced_features.py

cli-help:  ## 显示CLI帮助
	python -m meetaudio.cli --help

setup-env:  ## 设置环境变量示例
	@echo "请设置以下环境变量:"
	@echo "export BYTEDANCE_APP_KEY=your_app_key"
	@echo "export BYTEDANCE_ACCESS_KEY=your_access_key"
	@echo ""
	@echo "或者复制 .env.example 到 .env 并填入您的密钥"
