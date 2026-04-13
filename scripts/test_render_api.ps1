param(
    [string]$BaseUrl = "https://alter-sales-api-1.onrender.com",
    [string]$Username = "",
    [string]$Password = "",
    [switch]$IncludeIntake
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

if (-not ($Username -and $Password)) {
    throw "Defina -Username e -Password ou configure INBOUND_API_USERNAME e INBOUND_API_PASSWORD."
}

$pair = "{0}:{1}" -f $Username, $Password
$bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
$headers["Authorization"] = "Basic " + [Convert]::ToBase64String($bytes)

function Invoke-And-Print {
    param(
        [string]$Method,
        [string]$Url,
        [string]$Body = ""
    )

    Write-Host ""
    Write-Host "$Method $Url"

    if ($Body) {
        $response = Invoke-RestMethod -Method $Method -Uri $Url -Headers $headers -Body $Body
    } else {
        $response = Invoke-RestMethod -Method $Method -Uri $Url -Headers $headers
    }

    $response | ConvertTo-Json -Depth 10
}

Write-Host "BaseUrl: $BaseUrl"
Write-Host "Usuario: $Username"
Write-Host "Modo intake opcional: $IncludeIntake"

Invoke-And-Print -Method Get -Url "$BaseUrl/"
Invoke-And-Print -Method Get -Url "$BaseUrl/api/health"

if ($IncludeIntake) {
    Invoke-And-Print -Method Post -Url "$BaseUrl/api/sales/intake" -Body $payload
}

try {
    Invoke-And-Print -Method Get -Url "$BaseUrl/api/sales/latest"
} catch {
    Write-Host ""
    Write-Host "GET $BaseUrl/api/sales/latest"
    Write-Host $_
}

try {
    Invoke-And-Print -Method Get -Url "$BaseUrl/api/alter/feed/per-hour"
} catch {
    Write-Host ""
    Write-Host "GET $BaseUrl/api/alter/feed/per-hour"
    Write-Host $_
}

try {
    Invoke-And-Print -Method Get -Url "$BaseUrl/api/alter/feed/per-store"
} catch {
    Write-Host ""
    Write-Host "GET $BaseUrl/api/alter/feed/per-store"
    Write-Host $_
}
