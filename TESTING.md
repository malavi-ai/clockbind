# Testing record: ClockBind 1.2.0

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
| Web app | Real workbook in either loading order; exports PNG, SVG, CSV and print to PDF; damaged, empty, CSV and non-Bridge files; phone width (no sideways scroll); dark mode; offline after the first visit (service worker, 16 cached files) | pass |
| Studio | Every page; demo analyses; Output page PDF, Word and syntax downloads; Research checks in a real browser: upload, validate, PDF download, verdicts; results stay after a download | pass |
| Installation | Clean installs from the release zip on Python 3.9 (without chat tools), 3.10, 3.11, 3.12 and 3.13; Mac installer run end to end in a simulated home folder, with a newer Python and with Apple's 3.9 only; shell scripts checked with ShellCheck | pass |

## Not tested here
- Claude Desktop and Claude Code themselves (their configuration formats were tested, not the apps).
- A real Mac (the installer was simulated on Linux).
- Windows.
- The Hungarian and Persian interface texts were written by the developer with AI assistance; a native Hungarian speaker should proofread them.
