from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QSizePolicy,
)
from PySide6.QtGui import QPixmap

from app.widgets.page_thumbnail import PageThumbnailWidget
from app.core.thumbnail_worker import ThumbnailWorker


class FlowLayout(QVBoxLayout):
    """简单实现：用 QVBoxLayout 嵌套 QHBoxLayout 实现自动换行。"""
    pass


class ThumbnailGrid(QWidget):
    """可滚动的页面缩略图网格，支持异步加载。"""

    COLUMN_COUNT = 4

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
        self._grid_layout = None
        self._init_empty_grid()

        self._scroll.setWidget(self._container)
        outer.addWidget(self._scroll)

        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet("color: #666; font-size: 12px;")
        outer.addWidget(self._status_label)

    def _init_empty_grid(self):
        from PySide6.QtWidgets import QGridLayout
        if self._grid_layout:
            QWidget().setLayout(self._grid_layout)
        self._grid_layout = QGridLayout(self._container)
        self._grid_layout.setSpacing(8)
        self._grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

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
            row, col = divmod(i, self.COLUMN_COUNT)
            self._grid_layout.addWidget(thumb, row, col)

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
        pass  # 由 SplitTab 监听

    def clear(self):
        """停止渲染并清空所有缩略图。"""
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
            self._worker.wait(2000)
            self._worker = None

        self._thumbnails.clear()
        self._init_empty_grid()
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
