$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$configured = (Get-Content "$PSScriptRoot\config.json" -Raw | ConvertFrom-Json).project_root
if ($projectRoot -ne $configured) {
    Write-Warning "Extracted project root is '$projectRoot' but config points to '$configured'. RUN_LOOP uses config.json."
}
New-Item -ItemType Directory -Force -Path "$projectRoot\Reports\logs", "$projectRoot\Reports\receipts", "$projectRoot\Reports\results" | Out-Null
$openCode = Get-Command opencode -ErrorAction SilentlyContinue
if (-not $openCode) {
    throw "OpenCode was not found on PATH. Install OpenCode and reopen PowerShell."
}
& opencode --version
if ($LASTEXITCODE -ne 0) { throw "OpenCode exists but cannot start." }
& opencode auth list
if ($LASTEXITCODE -ne 0) { throw "OpenCode authentication check failed. Run: opencode auth login" }
if (-not (Test-Path "$projectRoot\AGENTS.md")) {
    Copy-Item "$PSScriptRoot\AGENTS.template.md" "$projectRoot\AGENTS.md"
} else {
    Write-Warning "AGENTS.md already exists; template was not allowed to overwrite it. Merge ResearchLoop\AGENTS.template.md manually if needed."
}
if (-not (Test-Path "$projectRoot\.opencode\commands\temp-drift-loop.md")) {
    throw "OpenCode command file is missing. Extract the ZIP directly into the project root and retry."
}
& "$PSScriptRoot\RUN_LOOP.ps1" -PreflightOnly
Write-Host "Installation PASS. Run 'opencode .' and then type '/temp-drift-loop'."
