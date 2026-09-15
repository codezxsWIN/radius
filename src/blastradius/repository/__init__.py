"""Safe repository acquisition for source-backed analysis."""

from .acquisition import acquire_repository
from .evidence import collect_repository_evidence

__all__ = ["acquire_repository", "collect_repository_evidence"]
