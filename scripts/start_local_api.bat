@echo off
setlocal

set "ROOT_DIR=%~dp0.."
set "API_PORT=%~1"
set "API_LOG=%~2"

if "%API_PORT%"=="" set "API_PORT=8091"
if "%API_LOG%"=="" set "API_LOG=%ROOT_DIR%\data\run_api.log"

cd /d "%ROOT_DIR%"
set "INBOUND_API_USERNAME="
set "INBOUND_API_PASSWORD="
set "DISABLE_INBOUND_AUTH=true"

echo Iniciando Alter Sales API em http://127.0.0.1:%API_PORT%
echo Log em: %API_LOG%
python -m uvicorn app.main:app --host 127.0.0.1 --port %API_PORT% 1>> "%API_LOG%" 2>>&1

echo.
echo A API foi encerrada. Veja o log em:
echo %API_LOG%
pause
