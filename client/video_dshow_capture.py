from __future__ import annotations

import platform
import threading
import time
import typing

import comtypes
import numpy as np
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QImage
from pygrabber.dshow_graph import FilterGraph


class DshowRgb24CaptureWorker(QObject):
    stream_started = Signal(int, int, float)
    frame_ready = Signal(QImage)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(
        self,
        device_name: str,
        width: int,
        height: int,
        target_fps: float | None = None,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self.device_name = device_name
        self.width = width
        self.height = height
        self.target_fps = target_fps
        self._stop_event = threading.Event()
        self._frame_event = threading.Event()
        self._frame_lock = threading.Lock()
        self._last_frame: np.ndarray | None = None
        self._graph: FilterGraph | None = None
        self._running: bool = False

    @Slot()
    def request_stop(self) -> None:
        self._stop_event.set()

    def _on_frame(self, frame: np.ndarray) -> None:
        with self._frame_lock:
            self._last_frame = frame
        self._frame_event.set()

    @staticmethod
    def _format_max_fps(fmt: dict[str, typing.Any]) -> float:
        return float(
            max(fmt.get("min_framerate", 0), fmt.get("max_framerate", 0))
        )

    @Slot()
    def run(self) -> None:
        if platform.system() != "Windows":
            self.error_occurred.emit("DirectShow only support windows.")
            self.finished.emit()
            return

        try:
            comtypes.CoInitialize()
            self._running = True

            graph = FilterGraph()
            self._graph = graph

            devices = graph.get_input_devices()
            if self.device_name not in devices:
                raise RuntimeError(
                    f"Video device not found: {self.device_name}"
                )
            device_index = devices.index(self.device_name)

            graph.add_video_input_device(device_index)
            video_input = graph.get_input_device()
            formats = video_input.get_formats()

            rgb24_formats = [
                fmt
                for fmt in formats
                if fmt["media_type_str"] == "RGB24"
                and fmt["width"] == self.width
                and fmt["height"] == self.height
            ]
            if not rgb24_formats:
                raise RuntimeError(
                    f"RGB24 format not found: {self.width}x{self.height}"
                )

            rgb24_formats.sort(key=self._format_max_fps, reverse=True)
            selected = rgb24_formats[0]
            selected_fps = self._format_max_fps(selected)
            if self.target_fps is not None:
                selected_fps = min(float(self.target_fps), selected_fps)
            if selected_fps <= 0:
                selected_fps = 60.0

            video_input.set_format(selected["index"])

            graph.add_sample_grabber(self._on_frame)
            graph.add_null_render()
            graph.prepare_preview_graph()
            graph.run()

            self.stream_started.emit(self.width, self.height, selected_fps)

            interval_s = 1.0 / float(selected_fps)
            if interval_s < 0.001:
                interval_s = 0.001
            next_ts = time.perf_counter()

            while not self._stop_event.is_set():
                next_ts += interval_s
                self._frame_event.clear()
                graph.grab_frame()
                self._frame_event.wait(timeout=interval_s)

                with self._frame_lock:
                    frame = self._last_frame
                    self._last_frame = None

                if frame is None:
                    continue

                frame = np.ascontiguousarray(frame)
                bytes_per_line = int(frame.shape[1] * frame.shape[2])
                image = QImage(
                    frame.data,
                    int(frame.shape[1]),
                    int(frame.shape[0]),
                    bytes_per_line,
                    QImage.Format.Format_BGR888,
                ).copy()
                self.frame_ready.emit(image)
                sleep_s = next_ts - time.perf_counter()
                if sleep_s > 0:
                    time.sleep(sleep_s)
        except Exception as exc:
            self.error_occurred.emit(str(exc))
        finally:
            try:
                if self._graph is not None:
                    self._graph.stop()
                    self._graph.remove_filters()
            except Exception:
                pass
            if self._running:
                try:
                    comtypes.CoUninitialize()
                except Exception:
                    pass
            self._running = False
            self.finished.emit()
