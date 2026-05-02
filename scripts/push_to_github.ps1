param(
    [string]$RemoteUrl = "https://github.com/PazParaTi/epifield-mpxv-dashboard.git"
)

Write-Host "Script run from: $(Get-Location)"
Write-Host "Remote: $RemoteUrl"

$Git = (Get-Command git -ErrorAction SilentlyContinue).Source
if (-not $Git -and (Test-Path -LiteralPath "C:\Program Files\Git\bin\git.exe")) {
    $Git = "C:\Program Files\Git\bin\git.exe"
}
if (-not $Git) {
    Write-Error "git n'est pas installe ou n'est pas dans le PATH. Installez Git for Windows et relancez ce script."
    exit 1
}

& $Git init
& $Git add .
& $Git commit -m "Initial commit"
& $Git branch -M main
if (-not (& $Git remote)) {
    & $Git remote add origin $RemoteUrl
}
& $Git push -u origin main
