# Privacy and data protection (GDPR · KVKK)

ClockBind is built so that research data stay with the researcher. This page describes what the software does with data, so that a data-protection officer, an ethics committee or a supervisor can check it. It is not legal advice. It is also not a certification: whether a study complies with the GDPR (Regulation (EU) 2016/679) or KVKK (Turkish Law No. 6698) depends on how the study is run. That includes its lawful basis, information to participants, approvals, storage and retention, and the controller stays responsible for those.

## What ClockBind does with data

| Part | Where data are processed | What is sent over the network |
|---|---|---|
| **Studio** (statistics app) | On your own computer. The app listens on `localhost` only and cannot be reached from other machines. | Nothing. Usage statistics are switched off. Fonts are bundled, so nothing is requested from font services. |
| **Command line** (`clockbind …`) | On your own computer. | Nothing, except `verify_references.py`, which you run yourself. It sends *reference metadata* (titles, DOIs) to Crossref/OpenAlex, never research data. |
| **Screening web app** (`ClockBind.html`, or https://malavi-ai.github.io/clockbind/) | Inside the browser on your device. Files are read with the browser's file API. | The files you open are never uploaded. The online version is hosted on GitHub Pages: opening it sends a normal web request (IP address, browser type) to GitHub, as any website visit does. Once installed, it runs offline and only checks GitHub for updates when you are online. The single file `ClockBind.html` makes no network requests at all. |
| **Chat tools** (MCP server, Claude plugin) | On your own computer: the chat app starts ClockBind locally and passes file paths. | The chat app receives the tool results: counts, levels, verdicts, check results and cell locations, plus file paths and pseudonymised episode codes. Cell values are never returned. Those results then go to the chat provider as part of the conversation, so use the tools only with files that are already pseudonymised, and follow your DPO's position on AI services. |
| **Word / Excel / syntax exports** | Written only where you save them. | Nothing. |
| **Run manifests and ledger** (command line) | Your output folder. | Nothing. They contain file hashes, software versions, parameters and column names. They do not contain data values. File names you choose are recorded, so do not put personal names in file names. |

Uploaded files are held in memory while the Studio is open. They are not copied into ClockBind's folders.

## Built-in safeguards

- **Personal-data scan.** When a file is opened in the Studio or the screening app, and with `clockbind privacy scan --data file.xlsx`, ClockBind looks for:
  - e-mail addresses, phone numbers, IBANs, payment-card numbers;
  - Turkish ID numbers (TCKN, checksum-verified) and Hungarian tax IDs;
  - columns whose name *and* content suggest names or identifiers (English, Turkish, Hungarian, Italian and Persian column names).

  It shows only the column, the kind of data and a count. Values are never displayed, stored or sent. The screening app marks the counts as *not citable* until those columns are pseudonymised. The scan is an aid: a clean result does not prove that a file is anonymous.
- **Pseudonymised codes by design.** The screening template uses codes (for example `EP-D01`, `Company A`). The key that links codes to real names belongs in a separate, protected file that is never loaded into ClockBind or any AI tool.
- **No research data in the software.** The repository, releases and Zenodo archive contain synthetic example data only.

## How this supports the legal principles

- **GDPR Art. 5(1)(c) data minimisation and Art. 89(1) research safeguards:** analyse pseudonymised codes only. The scan helps you spot what to remove.
- **GDPR Art. 25 data protection by design and by default:** local processing, no telemetry, no upload path, bundled fonts.
- **GDPR Art. 32 security of processing:** data never leave the device through ClockBind. Protect the device and the key file (disk encryption, access control).
- **International transfers (GDPR Chapter V; KVKK Art. 9):** ClockBind itself transfers no research data abroad. Opening the online web app contacts GitHub (a US provider); use the single offline file if even that must be avoided.
- **KVKK Art. 4 general principles and Art. 12 data security:** the same measures apply. Records whose KVKK clearance is still pending should not be opened for research at all.

## Checklist before analysing real data

1. Lawful basis, ethics approval and any DPO decision are documented. ClockBind does not provide these.
2. Direct identifiers are replaced with codes, and the key file is stored separately.
3. `clockbind privacy scan --data <file>` reports nothing, or each finding has been checked.
4. File names contain no personal names.
5. The analysis runs locally in the Studio or on the command line. Research data are never pasted into online services.
