"""Cooperative cancellation and truthful analysis stages for local reviews."""

from contextlib import contextmanager
from contextvars import ContextVar
from threading import Event
from time import monotonic

from ..model import GraphError


class AnalysisCancelled(GraphError):
    pass


class AnalysisOperation:
    def __init__(self, identifier, seconds=120):
        self.identifier = identifier
        self.cancelled = Event()
        self.deadline = monotonic() + seconds
        self.stage = "Starting analysis"
        self.finished = False

    def checkpoint(self, stage):
        if self.cancelled.is_set():
            raise AnalysisCancelled("Analysis cancelled. No partial result was retained.")
        if monotonic() >= self.deadline:
            raise AnalysisCancelled("Analysis deadline reached. No partial result was retained.")
        self.stage = stage


_active = ContextVar("repository_operation", default=None)


@contextmanager
def operation_scope(operation):
    token = _active.set(operation)
    try:
        yield
    finally:
        _active.reset(token)


def checkpoint(stage):
    operation = _active.get()
    if operation is not None:
        operation.checkpoint(stage)
