@echo off
setlocal
setlocal EnableDelayedExpansion

cd /d "%~dp0"

set "INBOUND_API_USERNAME="
set "INBOUND_API_PASSWORD="
set "DISABLE_INBOUND_AUTH=true"
set "API_PORT=8091"
set "ALTER_SALES_API_URL=http://127.0.0.1:%API_PORT%"
set "API_LOG=%~dp0data\run_api.log"

echo ========================================
echo Alter Sales API - Teste Local
echo ========================================
echo.
echo Usuario: sem autenticacao local
echo URL: %ALTER_SALES_API_URL%
echo.

echo [1/4] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
  echo ERRO: Python nao encontrado no PATH.
  pause
  exit /b 1
)

echo [2/4] Limpando porta %API_PORT% se ja existir processo antigo...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%API_PORT% .*LISTENING"') do (
  echo Encerrando PID %%P na porta %API_PORT%...
  taskkill /PID %%P /F >nul 2>&1
)

echo Subindo API local...
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
  echo ERRO: API nao respondeu em %ALTER_SALES_API_URL%/api/health
  echo Verifique a janela "Alter Sales API".
  echo.
  echo Ultimas linhas do log:
  powershell -ExecutionPolicy Bypass -Command "if (Test-Path '%API_LOG%') { Get-Content -Path '%API_LOG%' -Tail 40 }"
  pause
  exit /b 1
)

echo [3/4] Executando teste...
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\test_store_009_preview.ps1" -BaseUrl "%ALTER_SALES_API_URL%"
if errorlevel 1 (
  echo.
  echo ERRO: Falha ao executar o teste.
  echo Feche a janela "Alter Sales API" se ela ficou aberta.
  pause
  exit /b 1
)

echo.
echo [4/4] Consultando feed por loja...
powershell -ExecutionPolicy Bypass -Command ^
  "$headers = @{}; " ^
  "Invoke-RestMethod -Method Get -Uri '%ALTER_SALES_API_URL%/api/alter/feed/per-store' -Headers $headers | ConvertTo-Json -Depth 8"
if errorlevel 1 (
  echo.
  echo OBS: feed por loja nao ficou disponivel porque o store_alias_id ainda esta nulo.
  echo Isso e esperado nesse momento.
)

echo.
echo ========================================
echo Teste concluido
echo.
echo Se quiser encerrar a API, feche a janela:
echo Alter Sales API
echo ========================================
echo.
pause
