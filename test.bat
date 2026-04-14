@echo off
setlocal

echo Running mypy...
.venv\Scripts\python.exe -m mypy sim\config.py sim\world.py sim\render.py main.py tests/test_world.py tests/test_render.py
if errorlevel 1 goto :error

echo.
echo Running unit tests...
.venv\Scripts\python.exe -m unittest discover -s tests
if errorlevel 1 goto :error

echo.
echo All checks passed.
exit /b 0

:error
echo.
echo Checks failed.
exit /b 1
