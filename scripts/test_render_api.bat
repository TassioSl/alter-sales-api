@echo off
setlocal

set "ROOT=%~dp0.."
set "LOG_DIR=%ROOT%\logs"
set "LOG_FILE=%LOG_DIR%\test_render_api.log"
set "BASE_URL=https://alter-sales-api-1.onrender.com"
set /p "TEST_USERNAME=Usuario da API: "
set /p "TEST_PASSWORD=Senha da API: "
set /p "INCLUDE_INTAKE=Incluir POST /api/sales/intake com payload de exemplo? (s/N): "
set "EXTRA_ARGS="
if /I "%INCLUDE_INTAKE%"=="s" set "EXTRA_ARGS=-IncludeIntake"
if /I "%INCLUDE_INTAKE%"=="sim" set "EXTRA_ARGS=-IncludeIntake"

if not exist "%LOG_DIR%" (
  mkdir "%LOG_DIR%"
)

echo Executando teste da API publicada no Render...
echo Saida sera salva em:
echo %LOG_FILE%
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0test_render_api.ps1" -BaseUrl "%BASE_URL%" -Username "%TEST_USERNAME%" -Password "%TEST_PASSWORD%" %EXTRA_ARGS% > "%LOG_FILE%" 2>&1
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
