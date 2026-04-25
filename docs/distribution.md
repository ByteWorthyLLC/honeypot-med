# Distribution and Packaging

This project includes distribution-grade packaging and bootstrap scripts for macOS, Linux, and Windows.

## Native Package Build Scripts

- macOS: `scripts/package/build-macos.sh`
  - Outputs `.pkg` and `.tar.gz`
  - Requires `pkgbuild` (Xcode Command Line Tools)

- Linux: `scripts/package/build-linux.sh`
  - Always outputs `.tar.gz`
  - Optionally outputs `.deb` and `.rpm` when `fpm` is installed

- Windows: `scripts/package/build-windows.ps1`
  - Outputs portable `.zip`
  - Optionally outputs native installer `.exe` when Inno Setup (`iscc`) is installed

- Auto-select by platform: `scripts/package/build-release.sh`

## Container Distribution

- `Dockerfile`
- `docker-compose.yml`
- studio mode exposed on port `8899`
- capture mode exposed on port `8787`
- built-in image health check
- non-root runtime user

## CI Packaging

- Workflow: `.github/workflows/package.yml`
- Runs on Linux, macOS, and Windows
- Uploads built artifacts from `dist/`
- Smoke-tests packaged binaries before artifact upload
- Generates `dist/release-manifest.json`
- Generates `dist/SHA256SUMS.txt`

## Bootstrap Installers (Single Command)

### macOS / Linux

```bash
bash scripts/bootstrap/install.sh latest
```

Or from hosted release:

```bash
curl -fsSL https://raw.githubusercontent.com/<org>/<repo>/main/scripts/bootstrap/install.sh | bash -s -- latest
```

Environment variables:
- `HONEYPOT_MED_REPO` (default: `ByteWorthyLLC/honeypot-med`)
- `HONEYPOT_MED_INSTALL_DIR` (default: `~/.local/bin`)

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap/install.ps1 -Version latest
```

Or from hosted release:

```powershell
iwr https://raw.githubusercontent.com/<org>/<repo>/main/scripts/bootstrap/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File .\install.ps1 -Version latest
```

Parameters:
- `-Repo` (default: `ByteWorthyLLC/honeypot-med`)
- `-InstallDir` (default: `%LOCALAPPDATA%\Programs\HoneypotMed`)

## Post-Install

After installation:

```bash
honeypot-med start
honeypot-med doctor
```

If using direct `python app.py` from source, commands are the same:

```bash
python app.py start
python app.py doctor
```

For self-hosting instead of local source installs:

```bash
docker compose up --build studio
docker compose up --build capture
```
