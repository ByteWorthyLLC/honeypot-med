param(
  [string]$Version = "latest",
  [string]$Repo = "ByteWorthyLLC/honeypot-med",
  [string]$InstallDir = "$env:LOCALAPPDATA\Programs\HoneypotMed"
)

$ErrorActionPreference = "Stop"

if ($Version -eq "latest") {
  $tag = "latest"
  $latest = Invoke-WebRequest -Uri "https://api.github.com/repos/$Repo/releases/latest" -UseBasicParsing
  $latestObj = $latest.Content | ConvertFrom-Json
  $assetVersion = $latestObj.tag_name.TrimStart("v")
} else {
  $tag = "tags/$Version"
  $assetVersion = $Version.TrimStart("v")
}

$base = "https://github.com/$Repo/releases/$tag/download"
$tmp = Join-Path $env:TEMP "honeypot-med-install"
if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
New-Item -ItemType Directory -Path $tmp | Out-Null

$zipName = "honeypot-med-$assetVersion-windows-portable.zip"
$zipUrl = "$base/$zipName"
$zipFile = Join-Path $tmp $zipName

Write-Host "[bootstrap] downloading $zipUrl"
Invoke-WebRequest -Uri $zipUrl -OutFile $zipFile

if (Test-Path $InstallDir) { Remove-Item -Recurse -Force $InstallDir }
New-Item -ItemType Directory -Path $InstallDir | Out-Null
Expand-Archive -Path $zipFile -DestinationPath $InstallDir -Force

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (-not $userPath.Contains($InstallDir)) {
  [Environment]::SetEnvironmentVariable("Path", "$userPath;$InstallDir", "User")
  Write-Host "[bootstrap] added $InstallDir to user PATH"
}

Write-Host "[bootstrap] installed to $InstallDir"
Write-Host "[bootstrap] restart terminal, then run: honeypot-med.exe"
