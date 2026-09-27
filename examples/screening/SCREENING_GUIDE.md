# Bridge case screening — how to use `clockbind screen`

## Principle
The gates (criteria) live in a JSON file that you write and freeze **before** the final screening. The tool applies them to every row and reports whatever numbers result. It has **no target-count parameter**: it cannot be asked to "keep 19".

## Units and stages
- One row per **source entry** (email thread, document package, WhatsApp export …). Several entries can belong to one **episode** (`episode_id`).
- **S0 – analytic universe (entry level):** distinct source (not duplicate/staging/admin), organisational episode (not private use), inside the archive window, lawful research access (KVKK pending → `Unknown`, i.e. *held*, not excluded).
- **S1 – candidate episode (episode level):** materiality, reconstructable chronology, sufficient evidence, financing/payment architecture OR a comparator role defined before outcomes.
- **S2 – core case (episode level):** route evaluated, ex-ante timing, Tier A/B window, window documented before outcome, explicit required event R, mature outcome, triangulation, separable clocks, rivals coded.
- Optional second S2 **path** ("Mechanism core", Tier C allowed) — only if you decide so; see `gates_v2b_mechanism_DRAFT.json`.

## Integrity rules (v0.3, after independent audit 26 Sept 2026)
- Only values defined in the gates are accepted (case-insensitive: `y` → `Y`). Anything else (`Yes`, `PASS`, `TRUE`, `N/A`) is an **ERROR** and is treated as Unknown; a run with any ERROR is marked **NOT CITABLE**.
- Entry IDs must be unique (the run stops otherwise). Episode IDs differing only in case/spacing are merged and flagged.
- Conflicting values inside one episode → Hold (for every criterion type).
- Episodes are built from all non-excluded entries; values coded only on an excluded entry are flagged. Episodes whose entries are held at S0 (e.g. KVKK pending) appear as "Held at S0", never silently dropped.
- A criterion with `"gate": false` is recorded as a flag (e.g. censoring, rivals coded) and never moves a case down a level.
- A stage with several paths can map each path to a level (`levels_by_path`), so a Tier C path can never be labelled Level 3.
- `freeze` refuses names containing DRAFT, writes an append-only `FREEZE_REGISTER.jsonl` next to the gates file, and a version can be frozen only once. **The register is local: upload the gates file + register to OSF/Zenodo immediately for an external timestamp.**
- Every run is appended to `RUN_LEDGER.jsonl` (data hash, gates hash, counts, citable yes/no).
- Add a `source_author` column (own firm / buyer / third party / bank) to code evidential perspective.

## Coding values
`Y` pass · `N` fail · `Unknown` / `not documented` / blank → **Held** (missing evidence ≠ failure). A `PARTIAL` rating is coded `Unknown` until the missing element is resolved.
Episode-level values may be written on any one row of the episode; if two rows of the same episode disagree the tool reports an ERROR and holds the episode.

## Order of work
1. `clockbind screen template --gates gates_v2_DRAFT.json --output screening.xlsx` → blank sheet with dropdowns and a Definitions tab.
2. Edit the gates so labels and definitions match manuscript §3.1 word for word. **Decide** Tier C (path or no path).
3. `clockbind screen freeze --gates gates_v2.json --by "S. M. Alavi"` → date, name and sha256 are written into the file; record the USER DECISION line it prints. Any later edit is refused until you save a new `protocol_version`.
4. Fill the sheet from primary documents only (register row in `register_source`, written `reason` for every exclusion).
5. `clockbind screen run --data screening.xlsx --gates gates_v2.json` → `screening_result.xlsx` (Funnel, Episodes, Entries, Checks, Criteria), `flow_diagram.svg`, `funnel.md`, `manifest.json` (hashes of data and gates).
6. Fix every ERROR in *Checks* (conflicts, hand-typed status that disagrees with the gates, missing reasons) and re-run.
7. If a v1 protocol existed: `clockbind screen compare --data screening.xlsx --gates gates_v1.json --gates-b gates_v2.json` → list of episodes whose status changed; report it in the supplement.
8. Independent coder fills a copy blind; `clockbind screen agreement --data author.xlsx --coder coder.xlsx --gates gates_v2.json` → % agreement, Cohen's κ, Gwet's AC1 per criterion, and a disagreement list with a resolution-note column.

## Evidence-retrieval protocol (to avoid asymmetric search)
Apply the same retrieval to **every** candidate lacking an element: same sources (all company mailboxes, drives, bank statements, WhatsApp exports), same search terms (names/aliases, amounts, invoice numbers, dates ±60 days), same time budget. Log every search (date, source, terms, hits), including searches that found nothing.

## Files here
- `gates_v2_DRAFT.json`, `gates_v2b_mechanism_DRAFT.json` — drafts for your decision.
- `SYNTHETIC_*.xlsx` — invented test data (no real cases).
