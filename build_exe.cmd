@echo off
chcp 65001 >nul
cd /d "%~dp0"
pip install pyinstaller
del /f /q PromptManager.spec 2>nul
rmdir /s /q build_tmp 2>nul
pyinstaller --noconfirm --onefile --windowed --distpath . --workpath build_tmp --specpath . --add-data "templates;templates" --add-data "static;static" --name "PromptManager" app.py
rmdir /s /q build_tmp 2>nul
del /f /q PromptManager.spec 2>nul
echo Done! PromptManager.exe is ready.
pause
