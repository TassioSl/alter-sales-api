param(
    [string]$BaseUrl = "https://alter-sales-api-1.onrender.com",
    [string]$Username = "biomundo_api",
    [string]$Password = "B!oMundo_2026_R3nder_A7kP9xLm"
)

$ErrorActionPreference = "Stop"

$pair = "{0}:{1}" -f $Username, $Password
$token = [Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($pair))
$headers = @{ Authorization = "Basic $token" }

Write-Host ""
Write-Host "GET $BaseUrl/api/sales/latest"
Invoke-RestMethod -Uri "$BaseUrl/api/sales/latest" -Headers $headers | ConvertTo-Json -Depth 10

Write-Host ""
Write-Host "GET $BaseUrl/api/alter/feed/per-hour"
Invoke-RestMethod -Uri "$BaseUrl/api/alter/feed/per-hour" -Headers $headers | ConvertTo-Json -Depth 10

Write-Host ""
Write-Host "GET $BaseUrl/api/alter/feed/per-store"
Invoke-RestMethod -Uri "$BaseUrl/api/alter/feed/per-store" -Headers $headers | ConvertTo-Json -Depth 10
