param([switch]$PreflightOnly)
$ErrorActionPreference = "Stop"
$cfg = Get-Content "$PSScriptRoot\config.json" -Raw | ConvertFrom-Json
$argsList = @("$PSScriptRoot\tools\autoloop.py", "--repo", $cfg.project_root, "--config", "$PSScriptRoot\config.json")
if ($PreflightOnly) { $argsList += "--preflight-only" }
& $cfg.python @argsList
exit $LASTEXITCODE

