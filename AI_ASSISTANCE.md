# Disclosure of AI assistance

ClockBind was developed by Seyed Mehdi Alavi with the assistance of Claude (Anthropic), a large language model, which drafted code, tests and documentation under the author's direction (2026).

- Statistical computations use established libraries (NumPy, SciPy, statsmodels, ClockBind's own EFA module built on NumPy/SciPy, and R packages such as lavaan). ClockBind does not use AI at run time.
- Every procedure is checked against a reference implementation in R. The comparison is in `VALIDATION.md`, which is regenerated with `clockbind validate all`.
- The author is responsible for the design decisions, the validation and any use of the software in publications.
- No research data were shared in developing the software. Only synthetic data are included.
