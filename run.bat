@echo off
title MashalKitchen Online Food Ordering System
cls
echo ====================================================================
echo        MASHALKITCHEN - MODERN RESTAURANT ORDERING SYSTEM
echo        Location: Main Bazar, Chota Lahor, Swabi, KPK
echo        MySQL Database: food_order (with resilient fallback)
echo ====================================================================
echo  Web URL:      http://127.0.0.1:5000
echo  Menu:         http://127.0.0.1:5000/menu
echo  Cart:         http://127.0.0.1:5000/cart
echo  Orders:       http://127.0.0.1:5000/orders
echo  Admin Portal: http://127.0.0.1:5000/admin/login
echo  Credentials:  admin / admin123
echo ====================================================================
echo.

:: Try default python command
where python >nul 2>nul
if %errorlevel% equ 0 (
    python "app.py"
    goto end
)

:: Try py launcher
where py >nul 2>nul
if %errorlevel% equ 0 (
    py "app.py"
    goto end
)

:: Try Python 3.15 path
if exist "C:\Python315\python.exe" (
    "C:\Python315\python.exe" "app.py"
    goto end
)

echo [ERROR] Python was not found in PATH or standard installation directory!
echo Please ensure Python is installed and added to PATH.

:end
pause
