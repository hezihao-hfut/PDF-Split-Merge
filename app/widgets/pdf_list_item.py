from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QLineEdit


class PdfListItem(QWidget):
    """整合列表中的单个 PDF 项，显示文件名、页数、页码范围输入和移除按钮。"""

    remove_clicked = Signal(int)  # index
    page_range_changed = Signal(int, str)  # (index, range_text)

    def __init__(self, index: int, file_path: str, page_count: int, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.page_count = page_count
        self._index = index

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        import os
        name = os.path.basename(file_path)
        self._label = QLabel(f"{index + 1}. {name}  ({page_count} 页)")
        self._label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self._label, stretch=1)

        self._range_input = QLineEdit()
        self._range_input.setPlaceholderText("留空=全部")
        self._range_input.setFixedWidth(140)
        self._range_input.setStyleSheet("font-size: 12px; padding: 2px 4px;")
        self._range_input.textChanged.connect(
            lambda text: self.page_range_changed.emit(self._index, text)
        )
        layout.addWidget(self._range_input)

        btn = QPushButton("✕")
        btn.setFixedSize(24, 24)
        btn.setStyleSheet("border: none; color: #999; font-size: 14px;")
        btn.setCursor(self.cursor())
        btn.clicked.connect(lambda: self.remove_clicked.emit(self._index))
        layout.addWidget(btn)

    @property
    def page_range_text(self) -> str:
        return self._range_input.text().strip()

    def update_index(self, new_index: int):
        self._index = new_index
        import os
        name = os.path.basename(self.file_path)
        self._label.setText(f"{new_index + 1}. {name}  ({self.page_count} 页)")
