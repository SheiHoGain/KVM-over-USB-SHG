from __future__ import annotations

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QWidget


class VideoFrameWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._frame: QImage | None = None
        self._keep_aspect_ratio: bool = True
        self._flip_vertical: bool = False
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

    def set_keep_aspect_ratio(self, enable: bool) -> None:
        self._keep_aspect_ratio = enable
        self.update()

    def set_frame(self, frame: QImage | None) -> None:
        self._frame = frame
        self.update()

    def set_flip_vertical(self, enable: bool) -> None:
        self._flip_vertical = enable
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0))

        if self._frame is None or self._frame.isNull():
            painter.end()
            return

        target_rect = self.rect()
        if self._keep_aspect_ratio:
            frame_size = self._frame.size()
            frame_size.scale(
                target_rect.size(), Qt.AspectRatioMode.KeepAspectRatio
            )
            x = int((target_rect.width() - frame_size.width()) / 2)
            y = int((target_rect.height() - frame_size.height()) / 2)
            target_rect = QRect(x, y, frame_size.width(), frame_size.height())

        if self._flip_vertical:
            painter.save()
            painter.translate(0, self.height())
            painter.scale(1, -1)
            y = self.height() - target_rect.y() - target_rect.height()
            painter.drawImage(
                QRect(
                    target_rect.x(),
                    y,
                    target_rect.width(),
                    target_rect.height(),
                ),
                self._frame,
            )
            painter.restore()
        else:
            painter.drawImage(target_rect, self._frame)
        painter.end()
