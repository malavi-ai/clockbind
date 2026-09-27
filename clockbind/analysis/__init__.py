"""ClockBind analyses. Importing this package registers every analysis."""
from .core import REGISTRY, Output, outputs_to_docx, run, syntax_file  # noqa: F401
from . import basic, models, scales, doctoral  # noqa: F401,E402
