@echo off
setlocal

set "ROOT=%~dp0.."
set "LOG_DIR=%ROOT%\logs"
set "LOG_FILE=%LOG_DIR%\test_render_api.log"

if not exist "%LOG_DIR%" (
  mkdir "%LOG_DIR%"
)

echo Executando teste da API publicada no Render...
echo Saida sera salva em:
echo %LOG_FILE%
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0test_render_api.ps1" > "%LOG_FILE%" 2>&1
set "EXIT_CODE=%ERRORLEVEL%"

type "%LOG_FILE%"
echo.
echo Codigo de saida: %EXIT_CODE%
if not "%EXIT_CODE%"=="0" (
  echo O teste falhou. Revise a saida acima.
) else (
  echo O teste terminou com sucesso.
)

pause
exit /b %EXIT_CODE%
