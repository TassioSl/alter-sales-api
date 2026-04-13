param(
    [string]$BaseUrl = "http://127.0.0.1:8010",
    [string]$Username = "",
    [string]$Password = ""
)

$ErrorActionPreference = "Stop"

$payloadPath = Join-Path $PSScriptRoot "..\examples\store-009-conjunto-nacional.json"
$payload = Get-Content -Raw -Path $payloadPath

$headers = @{
    "Content-Type" = "application/json"
}

if (-not $Username) {
    $Username = $env:INBOUND_API_USERNAME
}

if (-not $Password) {
    $Password = $env:INBOUND_API_PASSWORD
}

if ($Username -and $Password) {
    $pair = "{0}:{1}" -f $Username, $Password
    $bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
    $headers["Authorization"] = "Basic " + [Convert]::ToBase64String($bytes)
}

Write-Host "Autenticando com usuario: $Username"
Write-Host "POST $BaseUrl/api/alter/preview/per-hour"
Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/alter/preview/per-hour" -Headers $headers -Body $payload | ConvertTo-Json -Depth 8

Write-Host ""
Write-Host "POST $BaseUrl/api/sales/intake"
Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/sales/intake" -Headers $headers -Body $payload | ConvertTo-Json -Depth 8

Write-Host ""
Write-Host "GET $BaseUrl/api/alter/feed/per-hour"
Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/alter/feed/per-hour" -Headers $headers | ConvertTo-Json -Depth 8
