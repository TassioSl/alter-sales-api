@echo off
setlocal

cd /d "%~dp0"

set "BASE_URL=https://alter-sales-api-1.onrender.com"
set "API_USERNAME=biomundo_api"
set "API_PASSWORD=B!oMundo_2026_R3nder_A7kP9xLm"
set "LOG_DIR=%~dp0logs"
set "LOG_FILE=%LOG_DIR%\teste_com_senha.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo Consultando API com autenticacao...
echo Saida sera salva em:
echo %LOG_FILE%
echo.

powershell -ExecutionPolicy Bypass -Command ^
  "$pair = '%API_USERNAME%:%API_PASSWORD%';" ^
  "$token = [Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($pair));" ^
  "$headers = @{ Authorization = 'Basic ' + $token };" ^
  "Write-Host ''; Write-Host 'GET %BASE_URL%/';" ^
  "Invoke-RestMethod -Uri '%BASE_URL%/' | ConvertTo-Json -Depth 10;" ^
  "Write-Host ''; Write-Host 'GET %BASE_URL%/api/health';" ^
  "Invoke-RestMethod -Uri '%BASE_URL%/api/health' -Headers $headers | ConvertTo-Json -Depth 10;" ^
  "Write-Host ''; Write-Host 'GET %BASE_URL%/api/sales/latest';" ^
  "try { Invoke-RestMethod -Uri '%BASE_URL%/api/sales/latest' -Headers $headers | ConvertTo-Json -Depth 10 } catch { $_ | Out-String | Write-Host };" ^
  "Write-Host ''; Write-Host 'GET %BASE_URL%/api/sales/latest?start_date=2026-04-01&end_date=2026-04-10';" ^
  "try { Invoke-RestMethod -Uri '%BASE_URL%/api/sales/latest?start_date=2026-04-01&end_date=2026-04-10' -Headers $headers | ConvertTo-Json -Depth 10 } catch { $_ | Out-String | Write-Host };" ^
  "Write-Host ''; Write-Host 'GET %BASE_URL%/api/alter/feed/per-hour';" ^
  "try { Invoke-RestMethod -Uri '%BASE_URL%/api/alter/feed/per-hour' -Headers $headers | ConvertTo-Json -Depth 10 } catch { $_ | Out-String | Write-Host };" ^
  "Write-Host ''; Write-Host 'GET %BASE_URL%/api/alter/feed/per-store';" ^
  "try { Invoke-RestMethod -Uri '%BASE_URL%/api/alter/feed/per-store' -Headers $headers | ConvertTo-Json -Depth 10 } catch { $_ | Out-String | Write-Host };" > "%LOG_FILE%" 2>&1

set "EXIT_CODE=%ERRORLEVEL%"
type "%LOG_FILE%"
echo.
echo Codigo de saida: %EXIT_CODE%
pause
exit /b %EXIT_CODE%
