# Changelog

## 1.3.0 — 2026-09-28 (Research Studio)
- 1.2.1 was not published separately; its changes are part of this release.
- The new Studio pages are available in English, Magyar and فارسی (Doctoral Programme, Publication and Statistics pages in English).
- **Doctoral Programme and Publication pages** in the Studio, spanning the Bridge study and Papers 1–4.
- **Paper 1 (DCE):** outside-option MNL, Swait–Louviere diagnostic, simulated-ML mixed logit and hierarchical-Bayes MNL, in addition to AMCE. MNL standard errors come from the observed information matrix (matches statsmodels ConditionalLogit).
- **Paper 2 (measurement):** HTMT, CR/AVE, incremental validity (ΔR²), group and longitudinal invariance via lavaan, follow-up attrition.
- **Paper 3:** T1/T2 first-difference models and dyadic discrepancy diagnostics; fsQCA (calibration, necessity, truth table, conservative solution) and Cox survival as exploratory tools. PRI follows Ragin's formula.
- **Paper 4 (qualitative):** case-code evidence matrices, provenance and chronology checks, conflicting evidence, process-tracing test register, governance-form comparison.
- **Publication:** local DRAFT/FROZEN preregistration snapshots with SHA-256, manuscript–result consistency audit, hashed submission bundles; no external registration is claimed.
- New Paper 1 mixed logit and HB, Paper 2 invariance and other new engines are marked **validation-required** until benchmarked against external reference implementations.
- **Research Studio Beta 2:** optional project manifests can preload governance, registered research assets, and privacy-minimised per-source/per-episode status registries on the Home dashboard. `CLOCKBIND_AUTO_PROFILE` supports a deliberate local project launcher without embedding private paths in the public package.
- **Audit false-positive controls:** current-wording checks can exempt archived/history sheet locations while privacy checks still run there; labelled-name detection requires an explicit field separator; the approved HUF 200,000 / HUF 200k materiality threshold is masked before generic amount detection.
- **Public package contains code, documentation, tests and synthetic examples only;** no study data.
- **Research Studio information architecture refresh:** persistent left navigation is now Home / Bridge / Statistics / Document Audit / Privacy / Reproducibility / Settings. Analysis work uses one five-stage interaction model: Upload → Configure → Run → Review → Export.
- **Bridge workspace:** workbook integrity, binding analysis and supervisor status are grouped under one Bridge module rather than mixed with statistics.
- **Document Audit and Privacy are separated:** methodological wording/version checks live in Document Audit; personal/confidential-data screening lives in Privacy. Both remain local and values are never displayed.
- **AI-safe research handoff:** `clockbind export ai-safe --workbook ... --gates ... --output ...` creates a zip containing aggregate Bridge status, protocol/code/input hashes and reproducibility metadata only—no cell values, raw document text, detected personal values or local input paths.
- **Chat/MCP surface expanded:** safe tools now include `bridge_validate`, `audit_documents`, `statistics_run`, `export_ai_safe` and `verify_package`, in addition to the existing binding, privacy, agreement and freeze tools.
- Fix: documents with no extractable text (empty or scanned) are listed as not read, never as clean.
- **Document audit, on this computer:** `clockbind audit docs --data <file | folder | zip>` and, in the Studio, the *Any personal data?* task now read Word, PDF, Excel, CSV, text and zip files (for example a Google Drive download). They report personal or confidential data (e-mails, phones, IBANs, ID numbers, card numbers, exact amounts, invoice or order numbers, and names from an optional local list) by kind and location only, never the value, and outdated wording against the Bridge rules of 28 September 2026 (`bridge_terms_2026-09-28.json`, editable). Results as Excel and PDF. The CLI now prints only aggregate counts by default, can write a safe `--summary-json`, exposes per-file names only with `--list-files`, recognises explicitly labelled person-name fields, and audits nested zip downloads with conservative archive limits.
- **Binding verdicts (Bridge protocol v3.4-DRAFT):** eight categories — Finance-, Payment-, Fulfilment-, Logistics-, Operational-readiness-binding, Jointly binding, Non-binding, Indeterminate. Step clocks must be finance, payment, fulfilment, logistics or operational-readiness (common synonyms such as supplier, delivery or installation are accepted); any other clock is reported as an input problem instead of being labelled "other".
- Protocol file `gates_v3.4_DRAFT.json`: finance-only actionability and the five-tier claim-language scale.

## 1.2.0 — 2026-09-28
- **New Studio, built around tasks.** A home screen shows where the Bridge study stands (sources reviewed, evidence levels, episodes held, workbook errors, roadmap A–E) and four large task cards: *Check my Bridge workbook*, *Which clock binds?*, *Any personal data?*, *Make a report*. Each task is a short step-by-step flow with plain-language fixes instead of technical check names. Statistics (Data, Analyze, Output, Cite) stay one click away.
- **Personal profiles on this computer.** Whoever uses the app picks their name; the greeting, language, workbook and protocol are remembered per person in `~/.clockbind/profiles.json`. No passwords and no online accounts.
- **Three languages:** English, Magyar and فارسی (right-to-left, Vazirmatn font bundled under the SIL Open Font Licence). Numbers are shown in Persian digits in the Persian interface.
- **Status report (PDF):** one click gives a dated project status for a supervisor or the study file.
- Stronger colour design; buttons and cards work at phone width.
- `clockbind.project` computes the project status (counts only; cell contents are not kept).
- 1.1.0 was not published separately; its changes are part of this release.

## 1.1.0 — 2026-09-27
- **Which clock binds?** New `clockbind binding` engine: counterfactual critical path over a dependency network with ex-ante expected durations; verdicts finance-binding, non-finance (named clock), jointly binding, non-binding, indeterminate; sign-stability rule for interval dates; finance actionability reported separately; reactive-downstream sensitivity. Timeline template with a synthetic example.
- **Workbook validation:** `clockbind workbook check` reports formula errors, uncalculated formulas, entries outside dropdown lists, episode/source links between sheets, override logs, verdict consistency and personal data. Locations only, never cell contents.
- **ClockBind in your chat:** local MCP server (`clockbind-mcp`) with research tools that return summaries only; `clockbind connect claude-desktop|show|status`; Claude Code plugin with slash commands and a working-rules skill (`.claude-plugin/marketplace.json`, `claude-plugin/`). Freezing gates from a chat requires explicit confirmation.
- **Redesign:** screening web app with section navigation, a status deck (episodes, personal data, checks, protocol), the evidence dial set as a faceted gem and a chat-tools panel; Studio gets a Research checks page (validate workbook, which clock binds, personal-data scan) and refined styling.
- Mac installer offers to connect ClockBind to Claude Desktop, and uses the newest Python 3 on the Mac (chat tools need 3.10+; Apple's 3.9 still installs everything else).
- **Exports:** PDF reports (bundled fonts) for workbook checks, screening runs, binding runs and Studio results; web app exports the levels dial (PNG), the screening flow (PNG, SVG, CSV), episodes and checks (CSV) and prints to PDF.
- Web app finds the assessment sheet and header row automatically (Bridge workbook: 05_Level_Assessment, header row 3); loading the protocol after the data re-reads the data; clear messages for damaged, empty or non-Excel files.
- Chat tools find the sheet and header row automatically; all commands give plain error messages instead of tracebacks (CLOCKBIND_DEBUG=1 shows details).
- Fix: an episode excluded as a whole (for example access refused) whose criteria are still PENDING no longer produces false "coded only on excluded entries" errors (Python and browser engines).
- Fix: dates such as 03.02.2026 are read day-first (3 February), Hungarian 2026. 02. 03. and Excel serial numbers are accepted, and ambiguous slashed dates are refused; mixed time-zone conventions, duplicate episodes, steps without an episode and missing columns are reported.
- Validation: binding engine cross-checked against an independent reference implementation on 2,000 random networks; browser engine parity extended to Bridge-structured workbooks (16 cases); tests pass on Python 3.9 (without chat tools) to 3.13.
- Screening protocol file `examples/screening/gates_v3.3_DRAFT.json`, matching the screening workbook (sheet 05_Level_Assessment, header row 3), with the registered binding rule and claim-ceiling definitions.
- `clockbind privacy scan` now scans every sheet of a workbook, not only the first.
- Personal-data scan no longer flags status labels such as "HUMAN PENDING" or "USER DECISION".
- Studio Cite page names the 1.0.1 version DOI.

## 1.0.1 — 2026-09-27 (10.5281/zenodo.22992952)
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

### 1.2.1 local statistics CLI addition
- Added auto-discovered `clockbind stats` plugin over the same analysis registry as ClockBind Studio.
- Added `list`, `show`, `columns`, `run`, and `batch` commands.
- Statistical runs remain local and write provenance manifests, frozen syntax, Word reports, Excel tables, and figure files where applicable.
- Added CLI regression tests, including a no-row-values metadata inspection test.
