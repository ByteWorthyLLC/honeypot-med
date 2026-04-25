param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$ArgsList
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Test-Path ".venv")) {
  py -m venv .venv
}

$python = Join-Path $root ".venv/Scripts/python.exe"
& $python -m pip install --upgrade pip | Out-Null
& $python -m pip install -e . | Out-Null

& $python app.py @ArgsList
exit $LASTEXITCODE
