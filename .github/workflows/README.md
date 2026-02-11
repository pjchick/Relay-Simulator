# GitHub Actions Workflows

This directory contains automated workflows for building and releasing Relay Simulator.

## Workflows

### 1. Build and Release (`build-release.yml`)

**Triggers:**
- When a version tag is pushed (e.g., `v1.0.0`, `v1.2.3`)
- Manually via GitHub Actions UI

**What it does:**
1. Builds Windows executable using PyInstaller
2. Creates a GitHub Release
3. Uploads the executable as a release asset

**How to create a release:**

```bash
# Create and push a version tag
git tag v1.0.0
git push origin v1.0.0
```

The workflow will automatically:
- Build the executable
- Create a release named "Relay Simulator v1.0.0"
- Attach `RelaySimulator.exe` to the release

**Manual trigger:**
1. Go to Actions → Build and Release
2. Click "Run workflow"
3. Select the branch
4. The artifact will be available for download but no release will be created

### 2. Build Test (`build-test.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**What it does:**
1. Tests that the build process works
2. Uploads the executable as an artifact (available for 7 days)
3. Does NOT create a release

**Purpose:**
Catch build issues early in development before creating official releases.

## Requirements

The workflows automatically install:
- Python 3.11
- PyInstaller
- All dependencies from `relay_simulator/requirements.txt`

## Build Process

Both workflows use the same build script: `build_exe.py`

The build:
- Creates a single-file Windows executable
- Includes all Python dependencies
- Runs without displaying a console window
- Typical size: 50-100 MB

## Release Versioning

Follow Semantic Versioning for tags:
- `v1.0.0` - Major release
- `v1.1.0` - Minor release (new features)
- `v1.1.1` - Patch release (bug fixes)

## Troubleshooting

### Build fails with missing dependencies
Check that `relay_simulator/requirements.txt` includes all required packages.

### Release creation fails
Ensure the repository has adequate permissions for the `GITHUB_TOKEN`.

### Executable fails to run
Test locally first:
```bash
python build_exe.py
dist\RelaySimulator.exe
```

## Notes

- **Windows Defender**: May flag PyInstaller executables as potentially unwanted. This is a false positive.
- **Build time**: Expect 3-5 minutes for the full workflow.
- **Artifacts**: Manual builds and test builds store artifacts for limited time.
