from __future__ import annotations

from PyQt6.QtCore import QEvent, QRect, QRectF, Qt, QUrl
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt6.QtWidgets import QWidget

from pocket_app.resources import Qss, ThemeManager, tr


class RoundedNetworkImage(QWidget):
    def __init__(
        self,
        url: str = "",
        *,
        parent: QWidget | None = None,
        width: int = 132,
        height: int = 132,
        radius: int = 18,
        circular: bool = False,
        failed_text: str = "",
    ) -> None:
        super().__init__(parent)
        self._url = ""
        self._radius = radius
        self._circular = circular
        self._manager = QNetworkAccessManager(self)
        self._pixmap: QPixmap | None = None
        self._reply: QNetworkReply | None = None
        self._request_id = 0
        self._has_requested = False
        self._failed = False
        self._placeholder_text = tr("image.empty")
        self._failed_text = failed_text.strip() or tr("image.failed")
        self.setMinimumSize(width, height)
        self.setFixedSize(width, height)
        ThemeManager.theme_changed.connect(self._on_theme_changed)
        self.set_url(url)

    def set_url(self, url: str) -> None:
        normalized = url.strip()
        if normalized == self._url and (self._pixmap is not None or self._has_requested):
            return
        self._url = normalized
        self._pixmap = None
        self._failed = False
        self._has_requested = False
        self._request_id += 1
        if self._reply is not None:
            self._reply.abort()
            self._reply.deleteLater()
            self._reply = None
        self._maybe_start_loading()
        self.update()

    def url(self) -> str:
        return self._url

    def clear(self) -> None:
        self.set_url("")

    def set_corner_radius(self, radius: int) -> None:
        self._radius = max(0, radius)
        self.update()

    def set_circular(self, circular: bool) -> None:
        self._circular = circular
        self.update()

    def is_circular(self) -> bool:
        return self._circular

    def set_placeholder_text(self, text: str) -> None:
        self._placeholder_text = text.strip() or tr("image.empty")
        self.update()

    def set_failed_text(self, text: str) -> None:
        self._failed_text = text.strip() or tr("image.failed")
        self.update()

    def failed_text(self) -> str:
        return self._failed_text

    def load_now(self) -> None:
        self._start_loading()

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self._maybe_start_loading()

    def moveEvent(self, event) -> None:  # type: ignore[override]
        super().moveEvent(event)
        self._maybe_start_loading()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._maybe_start_loading()

    def event(self, event) -> bool:  # type: ignore[override]
        if event.type() in (
            QEvent.Type.Polish,
            QEvent.Type.Paint,
            QEvent.Type.WindowActivate,
        ):
            self._maybe_start_loading()
        return super().event(event)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect())
        path = QPainterPath()
        radius = min(self.width(), self.height()) / 2 if self._circular else self._radius
        path.addRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)
        painter.setClipPath(path)

        bg, border, text = self._palette_colors()
        painter.fillPath(path, bg)

        if self._pixmap is not None and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = max(0, (scaled.width() - self.width()) // 2)
            y = max(0, (scaled.height() - self.height()) // 2)
            painter.drawPixmap(self.rect(), scaled, QRect(x, y, self.width(), self.height()))
        else:
            painter.setPen(text)
            painter.drawText(
                self.rect().adjusted(14, 14, -14, -14),
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                self._loading_text(),
            )

        painter.setClipping(False)
        painter.setPen(QPen(border, 1))
        painter.drawPath(path)
        event.accept()

    def _loading_text(self) -> str:
        if not self._url:
            return self._placeholder_text
        if self._failed:
            return self._failed_text
        if self._has_requested:
            return tr("image.loading")
        return tr("image.pending")

    def _palette_colors(self) -> tuple[QColor, QColor, QColor]:
        if ThemeManager.current_theme == Qss.Themes.DARK:
            return QColor("#1b2431"), QColor("#324255"), QColor("#8fa3bb")
        return QColor("#f2f6fb"), QColor("#d9e2ef"), QColor("#6b7c90")

    def _maybe_start_loading(self) -> None:
        if self._has_requested or not self._url or not self.isVisible():
            return
        if self._is_in_viewport():
            self._start_loading()

    def _is_in_viewport(self) -> bool:
        current = self.parentWidget()
        while current is not None:
            if current.objectName() == "qt_scrollarea_viewport":
                break
            current = current.parentWidget()

        if current is None:
            return True

        top_left = self.mapToGlobal(self.rect().topLeft())
        bottom_right = self.mapToGlobal(self.rect().bottomRight())
        self_rect = QRectF(top_left.x(), top_left.y(), bottom_right.x() - top_left.x(), bottom_right.y() - top_left.y())
        viewport_rect = current.rect()
        viewport_top_left = current.mapToGlobal(viewport_rect.topLeft())
        viewport_bottom_right = current.mapToGlobal(viewport_rect.bottomRight())
        visible_rect = QRectF(
            viewport_top_left.x(),
            viewport_top_left.y(),
            viewport_bottom_right.x() - viewport_top_left.x(),
            viewport_bottom_right.y() - viewport_top_left.y(),
        )
        return self_rect.intersects(visible_rect)

    def _start_loading(self) -> None:
        if self._has_requested or not self._url:
            return
        self._has_requested = True
        current_request_id = self._request_id
        request = QNetworkRequest(QUrl(self._url))
        reply = self._manager.get(request)
        if reply is None:
            self._failed = True
            self.update()
            return
        self._reply = reply
        reply.finished.connect(
            lambda current_id=current_request_id, current_reply=reply: self._finish_loading(
                current_id, current_reply
            )
        )
        self.update()

    def _finish_loading(self, request_id: int, reply: QNetworkReply) -> None:
        if request_id != self._request_id:
            reply.deleteLater()
            return

        self._reply = None
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            if pixmap.loadFromData(bytes(data)):
                self._pixmap = pixmap
                self._failed = False
            else:
                self._failed = True
        else:
            self._failed = True
        reply.deleteLater()
        self.update()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._reply is not None:
            self._reply.abort()
            self._reply.deleteLater()
            self._reply = None
        super().closeEvent(event)

    def _on_theme_changed(self, _theme: str) -> None:
        self.update()


def create_network_image(
    url: str = "",
    *,
    parent: QWidget | None = None,
    width: int = 132,
    height: int = 132,
    radius: int = 18,
    circular: bool = False,
    failed_text: str = "",
) -> RoundedNetworkImage:
    return RoundedNetworkImage(
        url,
        parent=parent,
        width=width,
        height=height,
        radius=radius,
        circular=circular,
        failed_text=failed_text,
    )
