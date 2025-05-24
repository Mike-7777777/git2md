@echo off
chcp 65001 >nul

echo 🚀 启动 Git2MD 应用...

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: Python 未安装
    echo 请先安装 Python 3.7+
    pause
    exit /b 1
)

REM 检查pip是否安装
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: pip 未安装
    pause
    exit /b 1
)

REM 创建虚拟环境（如果不存在）
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 🔧 激活虚拟环境...
call venv\Scripts\activate.bat

REM 升级pip
echo ⬆️  升级pip...
python -m pip install --upgrade pip

REM 安装依赖
echo 📥 安装依赖包...
pip install -r requirements.txt

REM 创建必要的目录
echo 📁 创建目录...
if not exist "downloads" mkdir downloads
if not exist "logs" mkdir logs

REM 检查环境变量文件
if not exist ".env" (
    if exist "env.example" (
        echo 📋 复制环境变量示例文件...
        copy env.example .env >nul
        echo ⚠️  请编辑 .env 文件设置您的配置
    )
)

REM 启动应用
echo 🌟 启动应用...
echo 应用将在 http://localhost:5000 运行
echo 按 Ctrl+C 停止应用
echo.

python app.py

pause 