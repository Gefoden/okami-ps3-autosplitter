@echo off
REM Activate your virtual environment
call env\Scripts\activate.bat

REM Build the exe directly in the root folder
pyinstaller --onefile --distpath . okami_ps3_autosplitter.py

echo Build finished!
pause
