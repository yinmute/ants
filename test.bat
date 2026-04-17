@echo off
setlocal

echo Running mypy...
.venv\Scripts\python.exe -m mypy sim\config.py sim\world.py sim\render.py sim\ant.py sim\sim.py main.py tests/test_world.py tests/test_render.py tests/test_ant.py tests/test_sim.py
if errorlevel 1 goto :error

echo.
echo Running unit tests with coverage...
.venv\Scripts\python.exe -m coverage run -m unittest discover -s tests
if errorlevel 1 goto :error

echo.
echo Coverage summary...
.venv\Scripts\python.exe -m coverage report -m
if errorlevel 1 goto :error

echo.
echo Writing HTML coverage report...
.venv\Scripts\python.exe -m coverage html
if errorlevel 1 goto :error

echo.
echo All checks passed.
exit /b 0

:error
echo.
echo Checks failed.
exit /b 1
