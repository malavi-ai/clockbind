---
description: Apply the registered screening gates (levels, funnel, flow diagram, integrity checks)
argument-hint: <workbook> <gates.json> [sheet] [header_row]
---
Run the ClockBind tool `screen_workbook` with these arguments: $ARGUMENTS
Leave sheet and header_row out unless the user gives them: the tool finds the assessment sheet and its header row automatically.

Report the funnel counts, the level counts and any integrity errors. If the gates are not frozen, state that the results are a draft and must not be reported as final.

The run folder also contains a PDF report (workbook_check.pdf, screening_report.pdf or binding_report.pdf). Give the researcher its full path so they can open or share it.
