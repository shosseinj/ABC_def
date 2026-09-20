$cfg = Get-Content "$PSScriptRoot\config.json" -Raw | ConvertFrom-Json
$reports = Join-Path $cfg.project_root "Reports"
New-Item -ItemType Directory -Force -Path $reports | Out-Null
Set-Content -Path (Join-Path $reports "STOP_REQUESTED") -Value (Get-Date).ToString("o")
Write-Host "A safe stop was requested. The loop will stop between agent attempts."

