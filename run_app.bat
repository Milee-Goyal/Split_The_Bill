@echo off
title SmartBill Server
cd /d "D:\Split the Bill From a Photograph"
echo Starting SmartBill Server at http://localhost:8000 ...
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause
