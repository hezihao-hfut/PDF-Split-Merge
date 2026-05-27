from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy


class PageThumbnailWidget(QWidget):
    """单个 PDF 页面缩略图控件，支持点击选中/取消。"""

    selection_changed = Signal(int, bool)  # (page_index, is_selected)

    THUMB_WIDTH = 150
    THUMB_HEIGHT = 200

    def __init__(self, page_index: int, parent=None):
        super().__init__(parent)
        self.page_index = page_index
        self._selected = False
        self._pixmap = None

        self.setFixedSize(self.THUMB_WIDTH + 12, self.THUMB_HEIGHT + 32)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 2)
        layout.setSpacing(2)

        self._image_label = QLabel()
        self._image_label.setFixedSize(self.THUMB_WIDTH, self.THUMB_HEIGHT)
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        layout.addWidget(self._image_label, alignment=Qt.AlignCenter)

        self._page_label = QLabel(f"第 {page_index + 1} 页")
        self._page_label.setAlignment(Qt.AlignCenter)
        self._page_label.setStyleSheet("font-size: 11px; color: #333;")
        layout.addWidget(self._page_label, alignment=Qt.AlignCenter)

    def set_pixmap(self, pixmap):
        self._pixmap = pixmap
        self._image_label.setPixmap(pixmap)

    @property
    def selected(self) -> bool:
        return self._selected

    @selected.setter
    def selected(self, value: bool):
        if self._selected == value:
            return
        self._selected = value
        self._update_border()
        self.selection_changed.emit(self.page_index, value)

    def toggle_selection(self):
        self.selected = not self.selected

    def _update_border(self):
        if self._selected:
            self._image_label.setStyleSheet(
                "background-color: #f0f0f0; border: 3px solid #2196F3;"
            )
        else:
            self._image_label.setStyleSheet(
                "background-color: #f0f0f0; border: 1px solid #ccc;"
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_selection()
        super().mousePressEvent(event)
