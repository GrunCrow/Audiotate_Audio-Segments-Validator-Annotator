# Maintainer guide: build and publish a release

This document is for maintainers publishing Audiotate desktop builds.

## What the workflow does

The `Build desktop executables` workflow builds a Windows x86_64 executable and a Linux x86_64 executable. A push to `main` or a manual workflow run produces downloadable Actions artifacts. A version tag matching `v*` also runs the release job, which creates or updates the GitHub Release and attaches the executables.

For the planned `v1.8.4` release, the files are named:

- `Audiotate-Windows-x86_64.exe`
- `Audiotate-Linux-x86_64.tar.gz`

## Publish a version

1. Update the application and citation versions for the release. For `v1.8.4`, the app version is `v1.8.4` in `config.py`, and the citation metadata uses `1.8.4`.
2. Commit and push all release changes to `main`. Confirm `.github/workflows/build-desktop.yml` is present on the default branch and that the source commit you want to release is on GitHub.
3. Check that the version tag does not already exist:

   ```powershell
   git tag --list v1.8.4
   ```

   If it prints `v1.8.4`, stop and inspect the existing tag; do not recreate or force-push it.

4. Create and push an annotated tag from the release commit:

   ```powershell
   git tag -a v1.8.4 -m "Release v1.8.4"
   git push origin v1.8.4
   ```

5. In GitHub, open **Actions → Build desktop executables** and follow the run. The `build` jobs must finish before the `release` job can attach the binaries. Confirm both files appear on the v1.8.4 release page.

Replace `v1.8.4` in these steps with the next version when preparing a later release.

## Manual build without publishing a release

Use **Actions → Build desktop executables → Run workflow** to build the current branch. This produces Actions artifacts, but it does not create a GitHub Release. To publish downloadable release assets, push a version tag as described above.

## Build and smoke-check Windows locally before pushing

From PowerShell with Python 3.11 installed, run:

```powershell
python -m venv .venv-build-run
.venv-build-run\Scripts\python.exe -m pip install -r requirements-build.txt
.venv-build-run\Scripts\pyinstaller.exe --clean --noconfirm app_windows.spec
.\dist\Audiotate-Windows-x86_64.exe
```

Wait for the app to open in your browser at `http://127.0.0.1:7864`. Confirm the page loads, then close the executable's console window. The build pins FastAPI and Starlette because newer releases changed the template API used by this Gradio version. The app also handles boolean JSON Schema values when Gradio creates API metadata.

## Troubleshooting

- A normal branch push does not publish a release; only a version tag matching `v*` runs the release job.
- If the workflow has no run, confirm the workflow file is on the default branch, Actions are enabled for the repository, and the pushed ref matches the trigger.
- If the Windows executable fails during Gradio import with a missing `gradio/blocks_events.pyc`, rebuild with the current `app_windows.spec`. Its `module_collection_mode={"gradio": "py"}` setting is required because Gradio reads component source files at import time.
- If the executable crashes while generating Gradio API metadata with `TypeError: argument of type 'bool' is not iterable`, rebuild from the current source. Gradio 4.44.1 / gradio-client 1.3.0 can pass boolean JSON Schema values to a parser that expects dictionaries; `app.py` includes a compatibility guard for this case. The guard must be included in the executable.
- If the executable fails while rendering the home page with `TypeError: unhashable type: 'dict'` in Jinja2, make sure the build used the FastAPI and Starlette versions pinned in `requirements-build.txt`; then rebuild in a clean Python 3.11 environment.
- If a build fails, inspect the failed platform job logs. Fix the source or packaging configuration, push the fix, and rerun the workflow for the same tag if the release has not completed.
- Do not force-move a published version tag. Use a new version for a corrected release.
