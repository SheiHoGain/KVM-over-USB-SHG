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
        a = float(fmt.get("min_framerate", 0) or 0)
        b = float(fmt.get("max_framerate", 0) or 0)
        if a <= 0 and b <= 0:
            return 0.0
        # 注意：部分 USB HDMI 采集卡驱动（包括 USB3 PLUS Video 这类）
        # 经常把 min_framerate / max_framerate 两个字段填反，
        # 会出现 "min_framerate"=60 / "max_framerate"=10 的情况。
        # 本函数要返回该格式可达到的帧率上限，因此直接取两者中的较大值，
        # 这样无论驱动字段顺序是否正确都能得到正确的最大帧率：
        #   驱动填反 (60, 10) -> 60 (正确, 与 OBS 表现一致)
        #   驱动正常 (30, 60) -> 60 (正确)
        return float(max(a, b))

    @Slot()
    def run(self) -> None:
        if platform.system() != "Windows":
            self.error_occurred.emit("DirectShow only support windows.")
            self.finished.emit()
            return

        first_frame_seen: bool = False
        first_frame_deadline_s: float = 0.0
        FIRST_FRAME_TIMEOUT_S: float = 4.0
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
            if self.target_fps is not None and self.target_fps > 0:
                selected_fps = min(float(self.target_fps), selected_fps)
            if selected_fps <= 0:
                selected_fps = 30.0

            video_input.set_format(selected["index"])

            graph.add_sample_grabber(self._on_frame)
            graph.add_null_render()
            graph.prepare_preview_graph()
            graph.run()

            self.stream_started.emit(self.width, self.height, selected_fps)

            interval_s = 1.0 / float(selected_fps)
            if interval_s < 0.001:
                interval_s = 0.001
            wait_timeout_s = max(interval_s * 3.0, 0.25)
            next_ts = time.perf_counter()
            first_frame_deadline_s = next_ts + FIRST_FRAME_TIMEOUT_S

            while not self._stop_event.is_set():
                next_ts += interval_s
                self._frame_event.clear()
                grab_ok = True
                try:
                    graph.grab_frame()
                except Exception:
                    if first_frame_seen:
                        raise
                    grab_ok = False
                if grab_ok:
                    self._frame_event.wait(timeout=wait_timeout_s)

                with self._frame_lock:
                    frame = self._last_frame
                    self._last_frame = None

                if frame is None:
                    if (
                        not first_frame_seen
                        and time.perf_counter() > first_frame_deadline_s
                    ):
                        raise RuntimeError(
                            "No video frame received within "
                            f"{FIRST_FRAME_TIMEOUT_S:.0f}s after "
                            "stream started. Check HDMI input signal, "
                            "resolution compatibility, or try a "
                            "smaller resolution."
                        )
                    continue
                first_frame_seen = True

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
