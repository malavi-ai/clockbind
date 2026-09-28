---
description: Which clock binds? Counterfactual verdicts from a timeline workbook (or create a blank template)
argument-hint: <timeline workbook .xlsx> | template <output path>
---
If the arguments start with "template", run `binding_template` with the output path that follows. Otherwise run `binding_verdicts` on: $ARGUMENTS

For verdicts, report per episode: verdict, binding clock(s), sign stability and finance actionability, and list any problems the tool found (missing dates, cycles, unknown predecessors). Explain that "Indeterminate" is a valid result under the sign-stability rule, not an error. Do not re-code or override verdicts; the researcher decides.

The run folder also contains a PDF report (workbook_check.pdf, screening_report.pdf or binding_report.pdf). Give the researcher its full path so they can open or share it.
