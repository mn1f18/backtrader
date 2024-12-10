@echo off
echo 正在安装依赖包...
call venv_backtrader\Scripts\activate.bat
python setup_env.py
pip install -r requirements.txt
echo 安装完成！
pause 