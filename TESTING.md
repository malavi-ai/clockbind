# Testing record: ClockBind 1.3.0

Tests run on 27–28 September 2026 before release. All tests were written by the developer; they show that ClockBind does what it was designed to do. They are not independent validation.

## Results

| Area | What was tested | Result |
|---|---|---|
| Statistics | 50 statistics compared with established R functions (`clockbind validate all`) | 50 of 50 pass |
| Binding rule | Engine compared with a separately written reference implementation (`validation/binding/reference.py`) on 2,000 random dependency networks with interval dates, missing durations and every verdict type | 2,000 of 2,000 identical |
| Binding rule | Hand-computed cases: finance-binding, jointly binding, non-binding, indeterminate (missing duration, missing date, sign change), window infeasible, parallel branches, cycles, unknown predecessors | pass |
| Binding input | Dates: ISO, date-time with offset, Excel date cells and serial numbers, 03.02.2026 (day first), 2026. 02. 03.; ambiguous 02/03/2026 refused; mixed time zones, duplicate episodes, orphan steps, missing columns reported | pass |
| Binding speed | 1,000 episodes | about 4 seconds |
| Browser engine | Same levels, counts and checks as the Python engine on 16 cases, including Bridge-structured workbooks (codes replaced) | 16 of 16 identical |
| Workbook check | Real v3.8 workbook; a copy with 7 injected errors (dropdown, duplicate ID, override without reason, verdict on a non-Level-3 episode, invalid level, unknown source, formula error); non-Bridge, empty, damaged, CSV and Persian-named files; 5,000-row workbook | all 7 injected errors found; clear messages for wrong files; 5,000 rows in about 14 seconds |
| Screening | Episode excluded as a whole with criteria still PENDING | no false errors (fixed in this release) |
| Privacy scan | Names (Turkish and Persian column names), e-mails, phone numbers, TCKN (checksum), IBAN; research codes, dates, amounts and status labels as false-positive probes | detections correct; no false positives on the probes |
| Chat tools (MCP) | All 9 tools over a real MCP connection, with good, missing, damaged, wrong-type and Persian-named files, automatic sheet detection, freeze confirmation, 7 parallel calls | no crash; plain messages; freeze refuses without confirmation |
| Claude Desktop link | `clockbind connect claude-desktop` on an existing config (other servers kept, backup made), invalid JSON left untouched | pass |
| Studio (new) | Profiles chooser, new profile, every page in English, Hungarian and Persian (AppTest and a real browser); Persian right-to-left layout; real study workbook: status and check flow; status PDF; statistics pages with demo analyses; phone width; every interface text present in all three languages with matching placeholders | pass |
| Document audit (new) | Synthetic Word file with an e-mail, phone, IBAN, invoice number, amount, listed name and outdated phrases; folder, zip and Google Docs shortcut; links, DOIs and ISBNs as false-positive probes; the study threshold (HUF 200,000) allowed; a revised manuscript with every outdated phrase removed | every planted item found; no value reported; revised manuscript clean; shortcut reported as not readable |
| Research Studio (new) | Real browser (Chromium): every left-navigation page (Home, Bridge, Statistics, Document Audit, Privacy, Reproducibility, Settings) in English, Hungarian and Persian with no errors; statistics workflow Upload → Configure → Run → Review → Export on the synthetic example | pass |
| AI-safe export (new) | Export on the synthetic workbook: aggregate counts, versions and SHA-256 only; no input path or cell value in the package | pass |
| Web app | Real workbook in either loading order; exports PNG, SVG, CSV and print to PDF; damaged, empty, CSV and non-Bridge files; phone width (no sideways scroll); dark mode; offline after the first visit (service worker, 16 cached files) | pass |
| Studio | Every page; demo analyses; Output page PDF, Word and syntax downloads; Research checks in a real browser: upload, validate, PDF download, verdicts; results stay after a download | pass |
| Installation | Clean installs from the release zip on Python 3.9 (without chat tools), 3.10, 3.11, 3.12 and 3.13; Mac installer run end to end in a simulated home folder, with a newer Python and with Apple's 3.9 only; shell scripts checked with ShellCheck | pass |

## Doctoral engines (1.3.0): focused validation — 29 September 2026

These checks cover the newly added doctoral-program engines. They are engineering validation, not independent methodological validation.

| Area | Focused check | Result |
|---|---|---|
| Paper 1 DCE | Outside-option MNL and two-condition Swait--Louviere diagnostic on synthetic conjoint data | pass |
| Paper 1 DCE | Simulated-ML mixed logit smoke test with Halton draws | pass; engine remains validation-required |
| Paper 1 DCE | Hierarchical-Bayes MNL Metropolis-within-Gibbs smoke test | pass; engine remains validation-required |
| Paper 2 | HTMT, incremental-validity ΔR², attrition and longitudinal-model syntax generation | pass |
| Paper 2 | lavaan group/longitudinal invariance runtime | not executed in this build environment because R/lavaan is unavailable; runtime gives an explicit dependency error |
| Paper 3 | fsQCA necessity/truth-table/conservative solution, T1/T2 first differences, Cox PH, dyad discrepancy | pass on synthetic data |
| Paper 4 | Case-code matrix, conflicting evidence and process-tracing register | pass on synthetic coded evidence |
| Publication | Draft preregistration bundle, SHA-256 manifest and row-level-data refusal | pass |
| CLI integration | P1, P2, P3 and P4 analyses invoked through `clockbind stats run`; Word/Excel/syntax/manifest outputs created | pass |
| New focused tests | `tests/test_doctoral_engines_beta3.py`, including MNL against statsmodels ConditionalLogit (estimates and standard errors) and PRI against Ragin's formula | 11 of 11 pass |
| Regression checks | Binding/reference | 13 of 13 pass |
| Regression checks | Workbook + AI-safe export | 5 of 5 pass |
| Regression checks | Document-audit CLI | 4 of 4 pass |
| Regression checks | Statistics CLI | 6 of 6 pass |
| Regression checks | Studio shell excluding live Streamlit launch | 8 of 8 pass, 1 deselected |

The complete legacy suite was not rerun as one uninterrupted process in this build environment because combined runs hit the execution-time ceiling. No claim is made that every legacy test completed in one Beta 3 run.

## Not tested here
- External reference-case agreement for the new mixed-logit and hierarchical-Bayes engines.
- Live R/lavaan execution of the new Paper 2 group and longitudinal invariance workflows in this build environment.
- Live visual end-to-end launch of the new Beta 3 Doctoral Programme and Publication pages; Python source compilation and non-launch Studio-shell regression tests passed.
- Claude Desktop and Claude Code themselves (their configuration formats were tested, not the apps).
- A real Mac (the installer was simulated on Linux).
- Windows.
- The Hungarian and Persian interface texts were written by the developer with AI assistance; a native Hungarian speaker should proofread them.
