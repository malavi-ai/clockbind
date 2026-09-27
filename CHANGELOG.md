# Changelog

## 1.0.1 — 2026-09-27
- Records the Zenodo DOIs: concept 10.5281/zenodo.22989932, version 1.0.0 10.5281/zenodo.22989933.
- DOI badge in README; Studio "Cite" page shows the DOI.
- ClockBind app for the Mac: the installer puts it in Applications; one click opens the Studio.
- Fix: `tabulate` added as a dependency (the screening report failed on a clean install).
- Installer no longer depends on where the folder is kept (regular install instead of editable).
- One-step publishing: upload a ClockBind zip to GitHub and the publish workflow unpacks it, makes the Release (Zenodo DOI) and updates the web app.
- Privacy (GDPR / KVKK): personal-data scan in the Studio, the screening app and `clockbind privacy scan` (values never shown); fonts bundled, so no requests to Google; PRIVACY.md.
- Web app built reproducibly from webapp/ sources (webapp/build.py); service worker updates automatically on each release.
- Screening app as an installable offline web app (docs/, GitHub Pages): add to Home Screen on iPhone, works without internet; files stay on the device.

## 1.0.0 — 2026-09-27 — first citable release (10.5281/zenodo.22989933)
- New ClockBind logo ("the open window"); brand theme file.
- Continuous testing on GitHub Actions; contributing guide.
- Validation: 50 of 50 statistics agree with R reference implementations.

## 0.5.0 — 2026-09-26
- Renamed from phdstat to ClockBind; `phdstat` command kept as alias.
- MIT licence, CITATION.cff, Zenodo metadata, AI-assistance disclosure.
- Analysis registry with reproducible syntax files; ClockBind Studio (local app); Word export.
- New modules: descriptives, crosstabs, mean comparisons, non-parametric tests, correlation, regression family, reliability, EFA, CFA (lavaan), charts.
- Validation suite against R with generated VALIDATION.md.

## 0.4.0 — 2026-09-26
- Browser app for Bridge screening (JavaScript engine, parity with Python on 14 cases).

## 0.3.x — 2026-09-26
- Screening integrity fixes after independent audit (freeze register, strict validation, levels, run ledger, code hash).
