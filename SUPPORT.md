# Support

## Primary Path

For normal usage, the simplest supported path is:

```bash
python app.py
```

Or, if you want the repository to bootstrap its own virtual environment first:

```bash
./run.sh
```

Windows:

```powershell
.\run.ps1
```

## Before Opening an Issue

Run:

```bash
python app.py doctor
python app.py share --pack claims --outdir reports/support-check
```

If Docker is your path:

```bash
docker compose up --build studio
```

## What To Include

- your OS
- whether you ran from source, packaged binary, or Docker
- the exact command
- the exact output or screenshot
- whether the failure happens in free local mode

