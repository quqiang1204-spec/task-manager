@echo off
chcp 65001 >nul
echo ================================
echo   日程任务管理系统
echo ================================
echo.
echo 正在启动...
echo.
streamlit run app.py --server.port 8501 --server.address localhost
pause
