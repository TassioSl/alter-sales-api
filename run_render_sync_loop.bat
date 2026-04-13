@echo off
setlocal

cd /d "%~dp0"

set "RENDER_URL=https://alter-sales-api-1.onrender.com"
set "STORE_CODE=9"
set "STORE_ALIAS_ID=9"
set "WAIT_SECONDS=600"
set "LOG_DIR=%~dp0logs"
set "LOOP_LOG=%LOG_DIR%\run_render_sync_loop.log"
set "SYNC_RESULT=%~dp0data\run_render_sync_result.json"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%~dp0data" mkdir "%~dp0data"

echo ========================================
echo Alter Sales API - Sync Render Loop
echo ========================================
echo URL: %RENDER_URL%
echo Loja: %STORE_CODE%
echo Store Alias ID: %STORE_ALIAS_ID%
echo Intervalo: %WAIT_SECONDS% segundos
echo Log: %LOOP_LOG%
echo.

set /p "API_USERNAME=Usuario da API Render: "
set /p "API_PASSWORD=Senha da API Render: "

:loop
for /f %%I in ('powershell -NoProfile -Command "(Get-Date).ToString(\"yyyy-MM-dd HH:mm:ss\")"') do set "NOW_TS=%%I"
for /f %%I in ('powershell -NoProfile -Command "(Get-Date).ToString(\"yyyy-MM-dd\")"') do set "RUN_DATE=%%I"

echo [%NOW_TS%] Iniciando sincronizacao... >> "%LOOP_LOG%"
echo.
echo [%NOW_TS%] Iniciando sincronizacao...

python .\scripts\load_real_store_009.py ^
  --start-date %RUN_DATE% ^
  --end-date %RUN_DATE% ^
  --store-code %STORE_CODE% ^
  --store-alias-id %STORE_ALIAS_ID% ^
  --mode intake ^
  --api-base-url %RENDER_URL% ^
  --api-username %API_USERNAME% ^
  --api-password %API_PASSWORD% > "%SYNC_RESULT%" 2>&1

if errorlevel 1 (
  echo [%NOW_TS%] ERRO no envio. >> "%LOOP_LOG%"
  type "%SYNC_RESULT%"
  type "%SYNC_RESULT%" >> "%LOOP_LOG%"
  echo.
  echo [%NOW_TS%] Aguardando %WAIT_SECONDS% segundos para nova tentativa...
  timeout /t %WAIT_SECONDS% /nobreak >nul
  goto :loop
)

type "%SYNC_RESULT%"
type "%SYNC_RESULT%" >> "%LOOP_LOG%"

echo. >> "%LOOP_LOG%"
for /f %%I in ('powershell -NoProfile -Command "(Get-Date).ToString(\"yyyy-MM-dd HH:mm:ss\")"') do set "HEALTH_TS=%%I"
echo [%HEALTH_TS%] Consultando health... >> "%LOOP_LOG%"

powershell -ExecutionPolicy Bypass -Command ^
  "$pair = '%API_USERNAME%:%API_PASSWORD%';" ^
  "$token = [Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($pair));" ^
  "$headers = @{ Authorization = 'Basic ' + $token };" ^
  "Invoke-RestMethod -Method Get -Uri '%RENDER_URL%/api/health' -Headers $headers | ConvertTo-Json -Depth 8" >> "%LOOP_LOG%" 2>&1

echo.
echo [%HEALTH_TS%] Sincronizacao concluida. Proxima execucao em %WAIT_SECONDS% segundos.
echo [%HEALTH_TS%] Sincronizacao concluida. Proxima execucao em %WAIT_SECONDS% segundos. >> "%LOOP_LOG%"
echo.
timeout /t %WAIT_SECONDS% /nobreak >nul
goto :loop
