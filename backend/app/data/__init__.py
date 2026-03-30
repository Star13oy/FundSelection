"""
Data management modules for fund historical data.

This package provides modules for fetching, storing, and retrieving
historical data for funds, including NAV time-series data.

Note: This package (app/data/) coexists with app.data.py module.
The FUNDS list is imported from the data.py module.
"""

# Import FUNDS from the legacy data.py module for backward compatibility
# Use absolute import to avoid circular import
import sys
import importlib.util
from pathlib import Path

# Load data.py module directly from file to avoid circular import
data_py_path = Path(__file__).parent.parent / "data.py"
spec = importlib.util.spec_from_file_location("app.data_module", data_py_path)
data_module = importlib.util.module_from_spec(spec)
sys.modules["app.data_module"] = data_module
spec.loader.exec_module(data_module)
FUNDS = data_module.FUNDS  # type: ignore

from app.data.nav_history import NAVHistoryManager

__all__ = ["FUNDS", "NAVHistoryManager"]
