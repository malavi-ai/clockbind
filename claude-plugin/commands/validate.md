---
description: Validate a screening workbook (formulas, dropdowns, cross-sheet links, overrides, verdicts, personal data)
argument-hint: <path to workbook .xlsx>
---
Run the ClockBind tool `validate_workbook` on this file: $ARGUMENTS

Then report, in the user's language:
1. The FAIL and WARN lines, grouped by sheet, with the exact location given by the tool.
2. For each problem, what the researcher should change (never change coding decisions yourself).
3. The run folder, so the researcher can open the full report.
If there are no FAIL lines, say so plainly. Do not ask the user to paste workbook contents into the chat.

The run folder also contains a PDF report (workbook_check.pdf, screening_report.pdf or binding_report.pdf). Give the researcher its full path so they can open or share it.
