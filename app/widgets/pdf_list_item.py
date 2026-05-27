from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton


class PdfListItem(QWidget):
    """整合列表中的单个 PDF 项，显示文件名、页数和移除按钮。"""

    remove_clicked = Signal(int)  # index

    def __init__(self, index: int, file_path: str, page_count: int, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.page_count = page_count
        self._index = index

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        import os
        name = os.path.basename(file_path)
        self._label = QLabel(f"{index + 1}. {name}  ({page_count} 页)")
        self._label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self._label, stretch=1)

        btn = QPushButton("✕")
        btn.setFixedSize(24, 24)
        btn.setStyleSheet("border: none; color: #999; font-size: 14px;")
        btn.setCursor(self.cursor())
        btn.clicked.connect(lambda: self.remove_clicked.emit(self._index))
        layout.addWidget(btn)

    def update_index(self, new_index: int):
        self._index = new_index
        import os
        name = os.path.basename(self.file_path)
        self._label.setText(f"{new_index + 1}. {name}  ({self.page_count} 页)")
