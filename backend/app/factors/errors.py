"""
Custom exceptions for factor calculation errors.

These exceptions provide detailed error information for debugging
and graceful error handling in the factor calculation pipeline.
"""


class FactorCalculationError(Exception):
    """Base exception for factor calculation errors."""
    pass


class InsufficientDataError(FactorCalculationError):
    """Raised when not enough historical data for calculations."""

    def __init__(self, fund_code: str, required: int, actual: int, metric: str = ""):
        self.fund_code = fund_code
        self.required = required
        self.actual = actual
        self.metric = metric
        message = f"Insufficient data for {fund_code}"
        if metric:
            message += f" {metric}"
        message += f": need {required} records, got {actual}"
        super().__init__(message)


class NAVDataError(FactorCalculationError):
    """Raised when NAV data is invalid or missing."""

    def __init__(self, fund_code: str, reason: str = ""):
        self.fund_code = fund_code
        self.reason = reason
        message = f"NAV data error for {fund_code}"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class BenchmarkDataError(FactorCalculationError):
    """Raised when benchmark data is unavailable."""

    def __init__(self, benchmark_code: str, reason: str = ""):
        self.benchmark_code = benchmark_code
        self.reason = reason
        message = f"Benchmark data error for {benchmark_code}"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class CalculationError(FactorCalculationError):
    """Raised when factor calculation fails for any reason."""

    def __init__(self, fund_code: str, operation: str, reason: str = ""):
        self.fund_code = fund_code
        self.operation = operation
        self.reason = reason
        message = f"Calculation error for {fund_code}: {operation}"
        if reason:
            message += f" - {reason}"
        super().__init__(message)
