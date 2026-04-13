@echo off
setlocal EnableDelayedExpansion

cd /d "%~dp0"

set "API_PORT=8091"
set "ALTER_SALES_API_URL=http://127.0.0.1:%API_PORT%"
set "API_LOG=%~dp0data\run_api.log"
set "STORE_CODE=9"
for /f %%I in ('powershell -NoProfile -Command "(Get-Date).ToString(\"yyyy-MM-dd\")"') do set "RUN_DATE=%%I"

echo ========================================
echo Alter Sales API - Teste Real
echo ========================================
echo Loja: %STORE_CODE%
echo Data usada no teste: %RUN_DATE%
echo URL: %ALTER_SALES_API_URL%
echo.

echo [1/5] Limpando porta %API_PORT% se ja existir processo antigo...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%API_PORT% .*LISTENING"') do (
  echo Encerrando PID %%P na porta %API_PORT%...
  taskkill /PID %%P /F >nul 2>&1
)

echo [2/5] Subindo API local...
if not exist "%~dp0data" mkdir "%~dp0data"
if exist "%API_LOG%" del "%API_LOG%"
start "Alter Sales API" cmd /c call "%~dp0scripts\start_local_api.bat" "%API_PORT%" "%API_LOG%"

echo Aguardando API iniciar...
set "READY="
for /l %%I in (1,1,15) do (
  powershell -ExecutionPolicy Bypass -Command ^
    "try { $r = Invoke-RestMethod -Method Get -Uri '%ALTER_SALES_API_URL%/api/health'; if ($r.status -eq 'ok') { exit 0 } else { exit 1 } } catch { exit 1 }"
  if not errorlevel 1 (
    set "READY=1"
    goto :api_ready
  )
  timeout /t 1 /nobreak >nul
)

:api_ready
if not defined READY (
  echo ERRO: API nao respondeu.
  powershell -ExecutionPolicy Bypass -Command "if (Test-Path '%API_LOG%') { Get-Content -Path '%API_LOG%' -Tail 40 }"
  pause
  exit /b 1
)

echo [3/5] Carregando vendas reais do DW...
python .\scripts\load_real_store_009.py --start-date %RUN_DATE% --end-date %RUN_DATE% --store-code %STORE_CODE% --mode intake --api-base-url %ALTER_SALES_API_URL% > "%~dp0data\run_real_result.json"
if errorlevel 1 (
  echo ERRO: Falha ao carregar vendas reais.
  pause
  exit /b 1
)

type "%~dp0data\run_real_result.json"

powershell -ExecutionPolicy Bypass -Command ^
  "$raw = Get-Content -Raw '%~dp0data\run_real_result.json' | ConvertFrom-Json; if ($raw.status -eq 'empty') { exit 20 } else { exit 0 }"
if errorlevel 20 (
  echo.
  echo Nenhuma venda real encontrada ainda para hoje. O teste terminou sem publicar lote vazio.
  echo.
  pause
  exit /b 0
)

echo.
echo [4/5] Consultando feed real por hora...
powershell -ExecutionPolicy Bypass -Command ^
  "Invoke-RestMethod -Method Get -Uri '%ALTER_SALES_API_URL%/api/alter/feed/per-hour' | ConvertTo-Json -Depth 8"

echo.
echo [5/5] Resumo do lote real...
python -c "from scripts.load_real_store_009 import build_payload; from datetime import date; sales=build_payload(date.fromisoformat('%RUN_DATE%'), date.fromisoformat('%RUN_DATE%'), %STORE_CODE%)['sales']; print('total_sales=', len(sales)); print('total_amount=', round(sum(float(s['total_amount']) for s in sales),2)); print('returns=', sum(1 for s in sales if s['return_id']))"

echo.
echo ========================================
echo Teste real concluido
echo ========================================
echo.
pause
