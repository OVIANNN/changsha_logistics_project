@echo off
rem ============================================================
rem  长沙物流运行态势分析 —— 交互式仪表盘启动脚本
rem  双击本文件即可启动，浏览器会自动打开仪表盘
rem ============================================================
chcp 65001 >nul
cd /d "%~dp0"

echo 正在启动 Streamlit 仪表盘...
echo 若浏览器未自动打开，请手动访问: http://localhost:8501
echo 按 Ctrl+C 可停止服务
echo.

streamlit run src\dashboard.py

pause
