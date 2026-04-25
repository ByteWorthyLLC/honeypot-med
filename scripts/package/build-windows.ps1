param(
  [string]$Python = "py",
  [string]$OutputDir = "dist/windows"
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
Set-Location $root

$version = & $Python -c "import sys;sys.path.insert(0,'src');import honeypot_med;print(honeypot_med.__version__)"
$venv = Join-Path $root ".release/.venv-package-windows"
$buildRoot = Join-Path $root ".release/windows"
$out = Join-Path $root $OutputDir

if (Test-Path $buildRoot) { Remove-Item -Recurse -Force $buildRoot }
if (Test-Path $out) { Remove-Item -Recurse -Force $out }

New-Item -ItemType Directory -Force -Path $buildRoot | Out-Null
New-Item -ItemType Directory -Force -Path $out | Out-Null

& $Python -m venv $venv
$venvPy = Join-Path $venv "Scripts/python.exe"

& $venvPy -m pip install --upgrade pip | Out-Null
& $venvPy -m pip install pyinstaller | Out-Null

& $venvPy -m PyInstaller --noconfirm honeypot-med.spec | Out-Null

$binary = Join-Path $root "dist/honeypot-med.exe"
$portable = Join-Path $out "honeypot-med-$version-windows-portable.zip"
Compress-Archive -Path $binary -DestinationPath $portable -Force
Write-Host "[windows] built portable package: $portable"

$inno = Get-Command iscc -ErrorAction SilentlyContinue
if ($null -ne $inno) {
  $iss = Join-Path $buildRoot "honeypot-med.iss"
  @"
[Setup]
AppName=Honeypot Med
AppVersion=$version
DefaultDirName={autopf}\\Honeypot Med
DefaultGroupName=Honeypot Med
OutputDir=$out
OutputBaseFilename=honeypot-med-$version-windows-installer
Compression=lzma
SolidCompression=yes

[Files]
Source: "$binary"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\\Honeypot Med"; Filename: "{app}\\honeypot-med.exe"

[Run]
Filename: "{app}\\honeypot-med.exe"; Description: "Run Honeypot Med"; Flags: nowait postinstall skipifsilent
"@ | Set-Content -Encoding UTF8 $iss

  & $inno.Source $iss | Out-Null
  Write-Host "[windows] built native installer in $out"
} else {
  Write-Host "[windows] Inno Setup (iscc) not found; skipped native installer"
}
