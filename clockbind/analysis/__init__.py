"""ClockBind analyses. Importing this package registers every analysis."""
from .core import REGISTRY, Output, outputs_to_docx, run, syntax_file  # noqa: F401
from . import basic, models, scales, doctoral, paper1, paper2, paper3, paper4  # noqa: F401,E402
