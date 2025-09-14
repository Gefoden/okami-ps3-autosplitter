@echo off
REM Activate your virtual environment
call env\Scripts\activate.bat

REM Build the exe directly in the root folder
pyinstaller --onefile --distpath . --icon=icon.ico okami_autosplitter.py

echo Build finished!
pause
