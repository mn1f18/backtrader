@echo off
echo === 开始设置环境和安装依赖包 ===

:: 检查 Python 是否安装
python --version > nul 2>&1
if errorlevel 1 (
    echo Python未安装，请先安装Python！
    pause
    exit /b
)

:: 检查虚拟环境是否存在
if not exist "venv_backtrader" (
    echo 创建虚拟环境...
    python -m venv venv_backtrader
)

:: 激活虚拟环境并安装包
echo 激活虚拟环境...
call venv_backtrader\Scripts\activate.bat

echo 升级pip...
python -m pip install --upgrade pip

echo 安装依赖包...
pip install -r requirements.txt

echo === 环境设置和包安装完成！===
pause 