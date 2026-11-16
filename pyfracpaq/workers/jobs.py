"""QObject jobs; all widget and figure updates remain on the main thread."""

from collections.abc import Callable
from dataclasses import dataclass
import logging

from PySide6.QtCore import QObject, QThread, Signal, Slot

from pyfracpaq.domain.execution import FieldError

LOG = logging.getLogger(__name__)
Operation = Callable[[Callable[[int, str], None], Callable[[], bool]], object]


@dataclass(frozen=True, slots=True)
class JobFailure:
    message: str
    field: str
    exception_type: str


class JobWorker(QObject):
    progress = Signal(int, str)
    result = Signal(object)
    failed = Signal(object)
    finished = Signal()

    def __init__(self, operation: Operation, default_field: str) -> None:
        super().__init__()
        self.operation = operation
        self.default_field = default_field

    @Slot()
    def run(self) -> None:
        thread = QThread.currentThread()
        try:
            result = self.operation(self.progress.emit, thread.isInterruptionRequested)
            if not thread.isInterruptionRequested():
                self.result.emit(result)
        except Exception as error:
            LOG.exception('Operation failed')
            field = error.field if isinstance(error, FieldError) else self.default_field
            self.failed.emit(JobFailure(str(error), field, type(error).__name__))
        finally:
            self.finished.emit()
