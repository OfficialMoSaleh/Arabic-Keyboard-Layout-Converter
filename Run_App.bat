@echo off
setlocal
cd /d "%~dp0windows-app"

rem Try pythonw (silent), python, pyw, py
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw app.py
    exit /b 0
)

where pyw >nul 2>nul
if %errorlevel%==0 (
    start "" pyw -3 app.py
    exit /b 0
)

where python >nul 2>nul
if %errorlevel%==0 (
    start "" python app.py
    exit /b 0
)

where py >nul 2>nul
if %errorlevel%==0 (
    start "" py app.py
    exit /b 0
)

start "" app.py
exit /b 0
