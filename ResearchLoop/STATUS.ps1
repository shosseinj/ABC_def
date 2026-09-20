$cfg = Get-Content "$PSScriptRoot\config.json" -Raw | ConvertFrom-Json
$status = Join-Path $cfg.project_root "Reports\status.json"
if (Test-Path $status) { Get-Content $status -Raw } else { Write-Host "No state yet. Run RUN_LOOP.ps1." }

