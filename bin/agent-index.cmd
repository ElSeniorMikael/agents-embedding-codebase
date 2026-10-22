@echo off
setlocal
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if not errorlevel 1 goto python
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if not errorlevel 1 goto py
>&2 echo agent-index: Python 3.10 or newer is required. Install Python and add python or py to PATH.
exit /b 1
:python
python "%~dp0agent-index" %*
exit /b %errorlevel%
:py
py -3 "%~dp0agent-index" %*
exit /b %errorlevel%
