# Making ClockBind citable (about 30 minutes, once)

1. **ORCID**: create a free iD at https://orcid.org and add it to CITATION.cff.
2. **GitHub**: create a free account, then a **public** repository named `clockbind`. Upload the contents of this folder. Never upload research data, code keys or company files; `.gitignore` excludes common data files.
3. **Zenodo**: sign in at https://zenodo.org with GitHub → Account → GitHub → switch on the `clockbind` repository.
4. **Release**: on GitHub → Releases → "Draft a new release" → tag `v1.0.0` (only after `clockbind validate all` passes and VALIDATION.md is committed) → Publish. Zenodo archives it and issues a DOI within minutes.
5. **Record the DOI** in CITATION.cff and README, and make a patch release.
6. **Cite in papers**: "Analyses were run in ClockBind v1.0.0 (Alavi, 2026; https://doi.org/10.5281/zenodo.22989933), which calls statsmodels 0.x (Seabold & Perktold, 2010) [and lavaan 0.6-x (Rosseel, 2012) for CFA]. Procedure-level validation against R is reported in the software's VALIDATION.md."
7. **Every new version gets its own DOI**, so a paper always points to the exact code that produced its numbers.

## One-step publishing (after the first release)
The repository has a `publish` workflow (`.github/workflows/publish.yml`). To publish a new version:
1. Raise `version` in `pyproject.toml` and `clockbind/__init__.py`, add a CHANGELOG section `## x.y.z`, then run `python webapp/build.py` (rebuilds the web app and the bundled data copies) and `python -m pytest tests`.
2. Upload the ClockBind zip (one top folder) at the repository root: **Add file → Upload files → Commit**.
3. The workflow checks the zip (exactly one folder, a ClockBind package; otherwise it removes the upload and stops with a message), makes the repository an exact copy of it, runs the tests, creates Release `vx.y.z` (Zenodo issues the version DOI) and redeploys the web app at https://malavi-ai.github.io/clockbind/.
One-time settings: Zenodo GitHub switch ON for the repository; GitHub **Settings → Pages → Source: GitHub Actions**.
