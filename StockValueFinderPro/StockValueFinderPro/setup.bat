@echo off
cd /d "%~dp0"
py -3.12 -m venv .venv || goto fail
.venv\Scripts\python.exe -m pip install --upgrade pip || goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt || goto fail
echo Setup complete. Run start.bat.
pause
exit /b 0
:fail
echo Setup failed. Check Python 3.12 and the error above.
pause
exit /b 1
