from __future__ import annotations

import inspect
import traceback
from collections.abc import Callable
from multiprocessing import Event, Process, Queue
from multiprocessing.synchronize import Event as SyncEvent
from typing import Any, Generic, TypeVar

from PySide6.QtCore import QObject, QRunnable, QTimer, Signal, Slot

R = TypeVar("R")


###############################################################################
class WorkerInterrupted(Exception):
    """Exception to indicate worker was intentionally interrupted."""

    pass


###############################################################################
class WorkerSignals(QObject):
    finished = Signal(object)
    error = Signal(tuple)
    interrupted = Signal()
    progress = Signal(int)


###############################################################################
class ThreadWorker(Generic[R], QRunnable):
    def __init__(self, fn: Callable[..., R], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self._is_interrupted = False

        signature = inspect.signature(fn)
        parameters = signature.parameters.values()

        if any(
            parameter.name == "progress_callback"
            or parameter.kind == inspect.Parameter.VAR_KEYWORD
            for parameter in parameters
        ):
            self.kwargs["progress_callback"] = self.signals.progress.emit

        if any(
            parameter.name == "worker" or parameter.kind == inspect.Parameter.VAR_KEYWORD
            for parameter in parameters
        ):
            self.kwargs["worker"] = self

    # -------------------------------------------------------------------------
    def stop(self) -> None:
        self._is_interrupted = True

    # -------------------------------------------------------------------------
    def is_interrupted(self) -> bool:
        return self._is_interrupted

    # -------------------------------------------------------------------------
    @Slot()
    def run(self) -> None:
        try:
            signature = inspect.signature(self.fn)
            parameters = signature.parameters
            if "progress_callback" not in parameters and "progress_callback" in self.kwargs:
                self.kwargs.pop("progress_callback")
            if "worker" not in parameters and "worker" in self.kwargs:
                self.kwargs.pop("worker")
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except WorkerInterrupted:
            self.signals.interrupted.emit()
        except Exception as exc:  # noqa: BLE001
            tb = traceback.format_exc()
            self.signals.error.emit((exc, tb))

    # -------------------------------------------------------------------------
    def cleanup(self) -> None:
        pass


###############################################################################
def _process_target(
    fn: Callable[..., R],
    args: Any,
    kwargs: Any,
    result_queue: Queue[Any],
    progress_queue: Queue[Any],
    interrupted_event: SyncEvent,
) -> None:
    try:
        signature = inspect.signature(fn)
        parameters = signature.parameters.values()

        if any(
            parameter.name == "progress_callback"
            or parameter.kind == inspect.Parameter.VAR_KEYWORD
            for parameter in parameters
        ):
            kwargs = dict(kwargs)
            kwargs["progress_callback"] = progress_queue.put

        if any(
            parameter.name == "worker" or parameter.kind == inspect.Parameter.VAR_KEYWORD
            for parameter in parameters
        ):

            class PlaceholderWorker:
                def is_interrupted(self) -> bool:  # type: ignore[override]
                    return interrupted_event.is_set()

            kwargs = dict(kwargs)
            kwargs["worker"] = PlaceholderWorker()

        result = fn(*args, **kwargs)
        result_queue.put(("finished", result))
    except WorkerInterrupted:
        result_queue.put(("interrupted", None))
    except Exception as exc:  # noqa: BLE001
        tb = traceback.format_exc()
        result_queue.put(("error", (exc, tb)))


###############################################################################
class ProcessWorker(QObject):
    _timer: QTimer | None

    def __init__(self, fn: Callable[..., R], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self._result_queue: Queue[Any] = Queue()
        self._progress_queue: Queue[Any] = Queue()
        self._interrupted = Event()
        self._process: Process | None = None
        self._timer = None

    # -------------------------------------------------------------------------
    def start(self) -> None:
        self._process = Process(
            target=_process_target,
            args=(
                self.fn,
                self.args,
                self.kwargs,
                self._result_queue,
                self._progress_queue,
                self._interrupted,
            ),
        )
        self._process.start()

        self._timer = QTimer()
        self._timer.timeout.connect(self.poll)
        self._timer.start(100)

    # -------------------------------------------------------------------------
    def stop(self) -> None:
        self._interrupted.set()

    # -------------------------------------------------------------------------
    def is_interrupted(self) -> bool:
        return self._interrupted.is_set()

    # -------------------------------------------------------------------------
    def poll(self) -> None:
        while not self._progress_queue.empty():
            try:
                progress = self._progress_queue.get_nowait()
                self.signals.progress.emit(progress)
            except Exception:  # noqa: BLE001
                pass

        if not self._result_queue.empty():
            status, payload = self._result_queue.get()
            if status == "finished":
                self.signals.finished.emit(payload)
            elif status == "error":
                self.signals.error.emit(payload)
            elif status == "interrupted":
                self.signals.interrupted.emit()

            if self._timer is not None:
                self._timer.stop()
            if self._process is not None:
                self._process.join()

    # -------------------------------------------------------------------------
    def cleanup(self) -> None:
        if self._timer is not None:
            self._timer.stop()
        if self._process is not None and self._process.is_alive():
            self._process.terminate()
            self._process.join()


###############################################################################
def check_thread_status(worker: ThreadWorker | ProcessWorker | None) -> None:
    if worker is not None and worker.is_interrupted():
        raise WorkerInterrupted()


###############################################################################
def update_progress_callback(
    progress: int, total: int, progress_callback: Any | None = None
) -> None:
    if progress_callback is not None and total:
        percent = int(progress * 100 / total)
        progress_callback(percent)
