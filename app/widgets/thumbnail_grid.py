from PySide6.QtCore import Qt, Slot, Signal, QSize, QRect, QPoint
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QSizePolicy, QLayout, QLayoutItem,
)
from PySide6.QtGui import QPixmap

from app.widgets.page_thumbnail import PageThumbnailWidget
from app.core.thumbnail_worker import ThumbnailWorker


class FlowLayout(QLayout):
    """根据可用宽度自动换行的流式布局。"""

    def __init__(self, parent=None, margin=0, h_spacing=8, v_spacing=8):
        super().__init__(parent)
        self._h_space = h_spacing
        self._v_space = v_spacing
        self._items: list[QLayoutItem] = []
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        m = self.contentsMargins()
        effective = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x = effective.x()
        y = effective.y()
        line_height = 0

        for item in self._items:
            wid = item.widget()
            space_x = self._h_space
            space_y = self._v_space
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > effective.right() + 1 and line_height > 0:
                x = effective.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y() + m.bottom()


class ThumbnailGrid(QWidget):
    """可滚动的页面缩略图网格，支持异步加载。"""

    selection_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thumbnails: list[PageThumbnailWidget] = []
        self._worker: ThumbnailWorker | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._container = QWidget()
        self._flow_layout = FlowLayout(self._container, margin=4, h_spacing=8, v_spacing=8)
        self._container.setLayout(self._flow_layout)

        self._scroll.setWidget(self._container)
        outer.addWidget(self._scroll)

        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet("color: #666; font-size: 12px;")
        outer.addWidget(self._status_label)

    def load_pdf(self, pdf_path: str):
        """加载 PDF 并异步渲染缩略图。"""
        self.clear()

        import fitz
        try:
            doc = fitz.open(pdf_path)
            page_count = doc.page_count
            doc.close()
        except Exception:
            self._status_label.setText("无法打开 PDF 文件")
            return

        self._status_label.setText(f"正在加载 {page_count} 页...")
        self._create_placeholder_thumbnails(page_count)

        self._worker = ThumbnailWorker(pdf_path)
        self._worker.page_ready.connect(self._on_page_ready)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _create_placeholder_thumbnails(self, count: int):
        self._thumbnails = []
        for i in range(count):
            thumb = PageThumbnailWidget(i, self)
            thumb.selection_changed.connect(self._on_selection_changed)
            self._thumbnails.append(thumb)
            self._flow_layout.addWidget(thumb)

    @Slot(int, QPixmap)
    def _on_page_ready(self, page_index: int, pixmap: QPixmap):
        if page_index < len(self._thumbnails):
            self._thumbnails[page_index].set_pixmap(pixmap)

    @Slot(str)
    def _on_error(self, msg: str):
        self._status_label.setText(f"渲染出错: {msg}")

    @Slot()
    def _on_finished(self):
        count = len(self._thumbnails)
        self._status_label.setText(f"共 {count} 页")

    def _on_selection_changed(self, page_index: int, selected: bool):
        self.selection_changed.emit()

    def clear(self):
        """停止渲染并清空所有缩略图。"""
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
            self._worker.wait(2000)
            self._worker = None

        self._thumbnails.clear()
        while self._flow_layout.count():
            item = self._flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._status_label.setText("")

    def get_selected_pages(self) -> list[int]:
        return [t.page_index for t in self._thumbnails if t.selected]

    def set_selected_pages(self, indices: list[int]):
        index_set = set(indices)
        for t in self._thumbnails:
            t.selected = t.page_index in index_set

    def select_all(self):
        for t in self._thumbnails:
            t.selected = True

    def deselect_all(self):
        for t in self._thumbnails:
            t.selected = False

    @property
    def page_count(self) -> int:
        return len(self._thumbnails)
