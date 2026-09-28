---
name: clockbind-research
description: Use when the user works on screening workbooks, case timelines, "which clock binds?" verdicts, coder agreement, personal-data checks or reference verification with ClockBind tools.
---

# Working with ClockBind

ClockBind runs on the researcher's computer. Its tools read files by path and return summaries only.

## Rules
- Pass file paths to the tools. Never ask the user to paste research data, names or amounts into the chat.
- The tools apply registered rules. They do not decide: the researcher codes criteria, approves overrides and resolves disagreements. Do not suggest changing a code to reach a level.
- Report results in the user's language, with the exact locations the tools give.
- "Indeterminate", "Held" and "PENDING" are valid results, not failures.
- Results from unfrozen gates are drafts. Say so.
- `freeze_gates` is permanent. Call it with confirm=true only after the researcher explicitly confirms in this conversation.
- Only references that `verify_references` marks as verified may be cited.

## Typical order
1. `privacy_scan` on any new file.
2. `validate_workbook` after each round of data entry; fix every FAIL.
3. `screen_workbook` for levels and the flow diagram.
4. After the freeze: `binding_template`, fill timelines, then `binding_verdicts`.
5. `coder_agreement` once the independent coder has finished.
