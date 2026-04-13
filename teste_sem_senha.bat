@echo off
setlocal

cd /d "%~dp0"

set "BASE_URL=https://alter-sales-api-1.onrender.com"
set "LOG_DIR=%~dp0logs"
set "LOG_FILE=%LOG_DIR%\teste_sem_senha.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo Consultando API sem autenticacao...
echo Saida sera salva em:
echo %LOG_FILE%
echo.

powershell -ExecutionPolicy Bypass -Command ^
  "Write-Host ''; Write-Host 'GET %BASE_URL%/';" ^
  "Invoke-RestMethod -Uri '%BASE_URL%/' | ConvertTo-Json -Depth 10;" ^
  "Write-Host ''; Write-Host 'GET %BASE_URL%/api/health';" ^
  "Invoke-RestMethod -Uri '%BASE_URL%/api/health' | ConvertTo-Json -Depth 10;" ^
  "Write-Host ''; Write-Host 'GET %BASE_URL%/api/sales/latest';" ^
  "try { Invoke-RestMethod -Uri '%BASE_URL%/api/sales/latest' | ConvertTo-Json -Depth 10 } catch { $_ | Out-String | Write-Host }" ^
  "Write-Host ''; Write-Host 'GET %BASE_URL%/api/alter/feed/per-hour';" ^
  "try { Invoke-RestMethod -Uri '%BASE_URL%/api/alter/feed/per-hour' | ConvertTo-Json -Depth 10 } catch { $_ | Out-String | Write-Host }" ^
  "Write-Host ''; Write-Host 'GET %BASE_URL%/api/alter/feed/per-store';" ^
  "try { Invoke-RestMethod -Uri '%BASE_URL%/api/alter/feed/per-store' | ConvertTo-Json -Depth 10 } catch { $_ | Out-String | Write-Host }" > "%LOG_FILE%" 2>&1

set "EXIT_CODE=%ERRORLEVEL%"
type "%LOG_FILE%"
echo.
echo Codigo de saida: %EXIT_CODE%
pause
exit /b %EXIT_CODE%
