@echo off
setlocal

set "LOG_DIR=%~dp0..\logs"
set "LOG_FILE=%LOG_DIR%\fetch_render_feeds_embedded.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo Consultando feeds do Render...
echo Saida sera salva em:
echo %LOG_FILE%
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0fetch_render_feeds_embedded.ps1" > "%LOG_FILE%" 2>&1
set "EXIT_CODE=%ERRORLEVEL%"

type "%LOG_FILE%"
echo.
echo Codigo de saida: %EXIT_CODE%
pause
exit /b %EXIT_CODE%
