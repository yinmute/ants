@echo off
setlocal

echo Creating virtual environment with Python 3.13...
py -3.13 -m venv .venv
if errorlevel 1 goto :error

echo Upgrading pip...
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto :error

echo Installing requirements...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo Setup complete.
echo Activate the environment with: .venv\Scripts\activate
echo Run the project with: run.bat
exit /b 0

:error
echo.
echo Setup failed.
exit /b 1
