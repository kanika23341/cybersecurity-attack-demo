@echo off
echo Starting target and attack pages...
start cmd /k "cd /d %~dp0food_delivery && pip install flask requests && python app.py"
start cmd /k "cd /d %~dp0attack_page && pip install flask requests && python app.py"
timeout /t 3 >nul
start http://127.0.0.1:5000
start http://127.0.0.1:5001
