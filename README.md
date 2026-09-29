<img src="clockbind/assets/clockbind-logo-horizontal.svg" width="360" alt="ClockBind — Which clock binds?">

# ClockBind
[![DOI](https://zenodo.org/badge/1390144757.svg)](https://doi.org/10.5281/zenodo.22989932)

**A local-first doctoral research operating system.** ClockBind combines evidence governance, Bridge classification, statistics, discrete-choice modelling, longitudinal measurement, configurational/panel analysis, qualitative case/process-tracing support, reproducibility and publication control.

**Beta 3 scientific-status note.** The previously released/core statistical procedures retain their existing validation record. The new Paper 1--4 engines added in Research Studio Beta 3 are functional but **validation-required** unless explicitly marked otherwise; convergence alone is never treated as validation.


| | |
|---|---|
| **Studio** | Local research workstation in English, Magyar or فارسی with persistent left navigation: **Home / Doctoral Programme / Bridge / Statistics / Document Audit / Privacy / Reproducibility / Publication**. Analysis modules follow **Upload → Configure → Run → Review → Export**. Data never leave your computer. |
| **Reproducible** | Every result carries its *syntax* (JSON). `clockbind syntax run` re-creates the whole output from the data file, with a manifest (data hash, software versions, code hash). |
| **Validation-aware** | `clockbind validate all` compares 50 core statistics with established R functions (50 of 50 pass; [VALIDATION.md](VALIDATION.md)). New Beta 3 DCE/HB/invariance/fsQCA/panel/survival/qualitative-support procedures carry explicit validation-required or methodological-support labels until frozen reference-case comparisons are completed. |
| **Private** | Everything runs on your device; no telemetry; bundled fonts; a personal-data scan warns before analysis (GDPR / KVKK). See [PRIVACY.md](PRIVACY.md). |
| **In your chat** | Connect ClockBind to Claude Desktop, Claude Code or any MCP chat app with one command. Your assistant runs the checks on files you name; only results come back (counts, levels, verdicts, cells to fix), never cell values. |
| **Tested** | See [TESTING.md](TESTING.md). The released/core procedures retain their prior validation record; Beta 3 adds focused engineering tests and explicitly identifies procedures still requiring external reference validation. |
| **Citable** | MIT licence, `CITATION.cff`, Zenodo DOI per release (see [RELEASE_GUIDE.md](RELEASE_GUIDE.md)). |

## Analyses
- **Data:** missing-data overview.
- **Descriptive statistics:** frequencies, descriptives (SPSS-style skewness/kurtosis), normality (Shapiro–Wilk, Q–Q), crosstabs (χ², likelihood ratio, Yates, Fisher, Cramér's V).
- **Compare means:** independent t-test (Student and Welch, Levene, Cohen's d); paired and one-sample t-tests; one-way ANOVA (Welch ANOVA, η², ω², Tukey HSD).
- **Non-parametric tests:** Mann–Whitney U, Wilcoxon signed-rank, Kruskal–Wallis.
- **Correlate:** Pearson, Spearman, Kendall, with CIs and a heat map.
- **Regression:**
  - linear: classical, HC3, cluster-robust CR1/CR2, weights, standardised β, VIF;
  - logistic: odds ratios, pseudo-R², classification table;
  - multinomial and ordinal.
- **Scale:** Cronbach's α and standardised α, McDonald's ω, item statistics; Cohen's κ, weighted κ, Gwet's AC1; ICC (6 types).
- **Dimension reduction:** EFA (KMO, Bartlett, scree, ML/minres/principal, varimax/oblimin/promax); CFA via **lavaan**, with fit indices, standardised loadings, AVE and CR.
- **Planning:** power and sample size (t, paired t, ANOVA, correlation, χ²).
- **Doctoral modules:**
  - Bridge screening with evidence levels;
  - *Which clock binds?* counterfactual critical-path verdicts with ex-ante durations, the sign-stability rule for interval dates and a reactive-downstream sensitivity check;
  - screening-workbook validation: formula errors, uncalculated cells, dropdown compliance, links between sheets, override logs, verdict consistency;
  - P3 multi-arm overlap weights (diagnostics, estimability gates, CR2 contrasts, cluster bootstrap);
  - P1 conjoint AMCEs with CR2 by respondent.
- **Paper 1 · DCE:** choice/design diagnostics; explicit outside-option MNL; Swait--Louviere relative-scale/preference-equality diagnostics; simulated-ML mixed logit; hierarchical-Bayes multinomial logit with respondent part-worths.
- **Paper 2 · Measurement:** construct reliability; HTMT; CR/AVE from supplied CFA loadings; incremental validity (ΔR²); configural/metric/scalar/partial-scalar invariance via lavaan; longitudinal T1/T2 invariance with correlated uniquenesses; 12-month attrition diagnostics.
- **Paper 3 · QCA & Panel:** fsQCA direct calibration; necessity analysis; truth tables; conservative minimisation without logical remainders; T1/T2 first-difference models; dyad discrepancy diagnostics; fsQCA and Cox survival are exploratory tools.
- **Paper 4 · Qualitative:** researcher-coded case × code evidence matrices; provenance and chronology coverage; conflicting/negative-evidence retention; process-tracing test register (straw-in-the-wind, hoop, smoking-gun, doubly decisive); governance-form cross-case matrices.
- **Publication & preregistration:** local hash-locked DRAFT/FROZEN snapshots, explicit manuscript-result consistency registries and hashed submission bundles. ClockBind never claims external OSF/registry submission.

## Screening app (any device, offline)
Open https://malavi-ai.github.io/clockbind/ once, then *Add to Home Screen* (iPhone) or *Install* (Chrome/Edge). After the first visit it works without internet. Files are read inside the browser and never uploaded. It covers case screening only; the statistics Studio runs on the Mac (below).

## Exports
- **Studio:** results as a Word document, a PDF report or a syntax file; Research checks as PDF, CSV or Excel.
- **Command line and chat tools:** every workbook check, screening run and binding run writes a PDF report next to its Excel results and manifest.
- **Screening web app:** levels dial as PNG; screening flow as PNG, SVG or CSV; episodes and checks as CSV; *Print or save as PDF* for the whole page. Everything is made in the browser; nothing is uploaded.

## ClockBind in your chat (Claude Desktop, Claude Code, any MCP app)
ClockBind includes a local tool server (Model Context Protocol). It runs on your computer and reads files by path; the chat receives summaries only.

- **Claude Desktop:** after installing ClockBind, run `clockbind connect claude-desktop` (the Mac installer offers this), then restart Claude Desktop.
- **Claude Code:** `/plugin marketplace add malavi-ai/clockbind`, then `/plugin install clockbind@clockbind`. Commands: `/clockbind:validate`, `/clockbind:privacy`, `/clockbind:screen`, `/clockbind:binding`, `/clockbind:agreement`, `/clockbind:refs`.
- **Other MCP apps:** `clockbind connect show` prints the configuration block to paste.

Needs Python 3.10 or later (the Mac installer uses the newest Python it finds; Apple's built-in 3.9 runs everything except the chat tools).

Tools include `bridge_validate`, `audit_documents`, `statistics_run`, `binding_verdicts`, `privacy_scan`, `export_ai_safe`, `doctoral_capabilities`, `preregistration_snapshot`, `publication_consistency_audit`, `verify_package`, `coder_agreement`, `freeze_gates` (asks for explicit confirmation), and `verify_references`. Full detailed results and manifests stay in `~/ClockBind_runs`; chat-facing responses are intentionally bounded.

If your study rules say that no case data may reach an AI tool (not even pseudonymised), use only `export_ai_safe`, `audit_documents` (aggregate counts) and `verify_package` with study files, and run everything else in the Studio or on the command line.

## Install (Mac)
1. Download the latest release from https://github.com/malavi-ai/clockbind/releases/latest (**Source code (zip)**) and unzip it.
2. In the folder, open **Install_ClockBind_on_Mac.command**. macOS asks because the file is not from the App Store:
   right-click → **Open** → **Open**. On macOS 15 or later, if there is no Open button: **System Settings → Privacy & Security → Open Anyway**.
3. When the Terminal says *Done*, **ClockBind** is in your Applications folder (Home → Applications). Drag it to the Dock: one click opens the Studio.

The Studio runs on your Mac and opens in your browser at `localhost:8501`; it works offline. R is optional for most of ClockBind, but required for CFA and the Paper 2 lavaan measurement-invariance workflows, and for re-running R-based validation.

## Command line
```
clockbind studio open                                   # the app
clockbind privacy scan --data data.xlsx                 # personal-data check (values never shown)
clockbind syntax list                                   # all analyses
clockbind syntax run --data data.xlsx --syntax my_syntax.json
clockbind screen run --data screening.xlsx --gates gates.json
clockbind workbook check --data screening.xlsx          # integrity before analysis or freeze
clockbind binding template --output timeline.xlsx      # timeline input with an example
clockbind binding run --data timeline.xlsx              # which clock binds? verdicts
clockbind export ai-safe --workbook Bridge.xlsx --gates gates.json --output Bridge_AI_Safe_Export.zip
clockbind connect claude-desktop                        # use ClockBind from your chat
clockbind validate all                                  # regenerate legacy/core VALIDATION.md
clockbind stats list                                    # Paper 1--4 + general statistics engines
clockbind publication prereg --file plan.json --output prereg.zip --status DRAFT
clockbind publication audit --manuscript paper.docx --registry result_registry.json
```
`phdstat` remains as an alias of `clockbind`.

## Checking documents before sharing
Everything runs on your computer; nothing is uploaded and values are never shown.

```
clockbind audit docs --data "Bridge download.zip"            # safe aggregate summary in the terminal
clockbind audit docs --data folder --names my_names.txt       # also look for names from your own local list
clockbind audit docs --data folder --summary-json summary.json # safe counts only; suitable to paste into a chat
clockbind audit docs --data folder --list-files               # opt in to local per-file names/statuses
```
In the Studio: **Bridge → Any personal data?** Drop Word, PDF, Excel, CSV, text or zip files. Google Docs must be downloaded first (select the files in Drive → Download gives a zip with Word/Excel copies). The CLI is safe-by-default: it prints aggregate counts only; file names are shown in the local Excel/PDF report, or in the terminal only with `--list-files`. Nested zip files are read locally with archive-size limits.

## Citing
> Alavi, S. M. (2026). *ClockBind: a reproducible statistics studio for doctoral research* (Version 1.0.1) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.22992952

Cite the exact version you used. Each release has its own version DOI; the concept DOI https://doi.org/10.5281/zenodo.22989932 always points to the latest version.

Source code: https://github.com/malavi-ai/clockbind

Please also cite the underlying libraries named in each result (statsmodels, SciPy, lavaan, …).

## Principles and limits
- Computations come from established libraries. ClockBind adds the interface, provenance and validation; no AI runs inside the software.
- Missing data: listwise deletion by default. Pre-specify your rule (e.g. multiple imputation) before analysing outcomes; multiple imputation is planned.
- Cluster-robust tests use G − 1 degrees of freedom. clubSandwich uses Satterthwaite df, so p-values can differ slightly with few clusters even when SEs agree.
- The P3 simulation assumptions (`clockbind/dgp`) are placeholders, not findings.
- ClockBind now supports structured qualitative evidence matrices and process-tracing registers, but it is not a replacement for full CAQDAS functions such as transcript annotation, multimedia coding or team codebook management in MAXQDA/NVivo/ATLAS.ti.
- New Beta 3 confirmatory engines must be externally benchmarked on frozen validation cases before they are used as sole support for manuscript claims.

Developed with the assistance of Claude (Anthropic); see [AI_ASSISTANCE.md](AI_ASSISTANCE.md). MIT licence.

## Local statistics CLI

ClockBind 1.2.1 exposes the same registered analyses used by Studio through an auto-discovered `stats` plugin. Data stay on the local computer.

```bash
clockbind stats list
clockbind stats show t_independent
clockbind stats columns --data study.xlsx
clockbind stats run --data study.xlsx --analysis descriptives --param variables=age,bp
clockbind stats run --data study.xlsx --analysis t_independent --param variables=outcome --param group=arm
clockbind stats batch --data study.xlsx --syntax analysis_plan.json
```

Each statistical run writes a provenance manifest and frozen syntax. Table-producing analyses also write `tables.xlsx`; figures are exported as PNG; all analyses are assembled into `output.docx`. `stats columns` prints only metadata (column names, dtypes, non-missing counts and unique counts), not row values.
