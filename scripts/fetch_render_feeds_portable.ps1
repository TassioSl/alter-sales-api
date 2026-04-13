param(
    [string]$BaseUrl = "https://alter-sales-api-1.onrender.com"
)

$ErrorActionPreference = "Stop"

$Username = Read-Host "Usuario da API"
$SecurePassword = Read-Host "Senha da API" -AsSecureString
$Password = [System.Net.NetworkCredential]::new("", $SecurePassword).Password

$pair = "{0}:{1}" -f $Username, $Password
$token = [Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($pair))
$headers = @{ Authorization = "Basic $token" }

function Invoke-And-Show {
    param(
        [string]$Url
    )

    Write-Host ""
    Write-Host "GET $Url"
    Invoke-RestMethod -Uri $Url -Headers $headers | ConvertTo-Json -Depth 10
}

Invoke-And-Show -Url "$BaseUrl/api/sales/latest"
Invoke-And-Show -Url "$BaseUrl/api/alter/feed/per-hour"
Invoke-And-Show -Url "$BaseUrl/api/alter/feed/per-store"
