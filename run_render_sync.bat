@echo off
setlocal

cd /d "%~dp0"

set "RENDER_URL=https://alter-sales-api-1.onrender.com"
set "STORE_CODE=9"
set "STORE_ALIAS_ID=9"
for /f %%I in ('powershell -NoProfile -Command "(Get-Date).ToString(\"yyyy-MM-dd\")"') do set "RUN_DATE=%%I"

echo ========================================
echo Alter Sales API - Sync Render
echo ========================================
echo URL: %RENDER_URL%
echo Loja: %STORE_CODE%
echo Store Alias ID: %STORE_ALIAS_ID%
echo Data: %RUN_DATE%
echo.

set /p "API_USERNAME=Usuario da API Render: "
set /p "API_PASSWORD=Senha da API Render: "

if not exist "%~dp0data" mkdir "%~dp0data"

echo [1/4] Consultando vendas reais do DW e enviando para o Render...
python .\scripts\load_real_store_009.py ^
  --start-date %RUN_DATE% ^
  --end-date %RUN_DATE% ^
  --store-code %STORE_CODE% ^
  --store-alias-id %STORE_ALIAS_ID% ^
  --mode intake ^
  --api-base-url %RENDER_URL% ^
  --api-username %API_USERNAME% ^
  --api-password %API_PASSWORD% > "%~dp0data\run_render_sync_result.json"

if errorlevel 1 (
  echo ERRO: Falha ao enviar vendas reais para o Render.
  if exist "%~dp0data\run_render_sync_result.json" type "%~dp0data\run_render_sync_result.json"
  pause
  exit /b 1
)

type "%~dp0data\run_render_sync_result.json"

powershell -ExecutionPolicy Bypass -Command ^
  "$raw = Get-Content -Raw '%~dp0data\run_render_sync_result.json' | ConvertFrom-Json; if ($raw.status -eq 'empty') { exit 20 } else { exit 0 }"
if errorlevel 20 (
  echo.
  echo Nenhuma venda real encontrada para hoje. Nada foi publicado.
  echo.
  pause
  exit /b 0
)

echo.
echo [2/4] Testando /api/health no Render...
powershell -ExecutionPolicy Bypass -Command ^
  "$pair = '%API_USERNAME%:%API_PASSWORD%';" ^
  "$token = [Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($pair));" ^
  "$headers = @{ Authorization = 'Basic ' + $token };" ^
  "Invoke-RestMethod -Method Get -Uri '%RENDER_URL%/api/health' -Headers $headers | ConvertTo-Json -Depth 8"

echo.
echo [3/4] Testando /api/alter/feed/per-hour no Render...
powershell -ExecutionPolicy Bypass -Command ^
  "$pair = '%API_USERNAME%:%API_PASSWORD%';" ^
  "$token = [Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($pair));" ^
  "$headers = @{ Authorization = 'Basic ' + $token };" ^
  "Invoke-RestMethod -Method Get -Uri '%RENDER_URL%/api/alter/feed/per-hour' -Headers $headers | ConvertTo-Json -Depth 8"

echo.
echo [4/4] Testando /api/alter/feed/per-store no Render...
powershell -ExecutionPolicy Bypass -Command ^
  "$pair = '%API_USERNAME%:%API_PASSWORD%';" ^
  "$token = [Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($pair));" ^
  "$headers = @{ Authorization = 'Basic ' + $token };" ^
  "Invoke-RestMethod -Method Get -Uri '%RENDER_URL%/api/alter/feed/per-store' -Headers $headers | ConvertTo-Json -Depth 8"

echo.
echo ========================================
echo Sync Render concluido
echo ========================================
echo.
pause
