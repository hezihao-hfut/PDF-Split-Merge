import os

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QFileDialog, QMessageBox, QGroupBox, QSizePolicy,
)

from app.widgets.thumbnail_grid import ThumbnailGrid
from app.utils.page_range_parser import parse_page_ranges, indices_to_range_text
from app.core.pdf_engine import PdfEngine


class SplitTab(QWidget):
    """PDF 切分页：左侧缩略图网格 + 右侧控制面板。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pdf_path: str | None = None
        self._page_count: int = 0
        self._updating_from_code = False

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # 左侧：缩略图网格
        self._grid = ThumbnailGrid()
        self._grid.setMinimumWidth(500)
        self._grid.selection_changed.connect(self._on_grid_selection_changed)
        main_layout.addWidget(self._grid, stretch=1)

        # 右侧：控制面板
        right_panel = QWidget()
        right_panel.setFixedWidth(300)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(12)

        # 加载按钮 + 文件信息
        load_group = QGroupBox("文件")
        load_layout = QVBoxLayout(load_group)
        self._load_btn = QPushButton("加载 PDF")
        self._load_btn.clicked.connect(self._load_pdf)
        load_layout.addWidget(self._load_btn)
        self._file_label = QLabel("未加载文件")
        self._file_label.setStyleSheet("color: #666; font-size: 12px;")
        self._file_label.setWordWrap(True)
        load_layout.addWidget(self._file_label)
        right_layout.addWidget(load_group)

        # 页码范围输入
        range_group = QGroupBox("页码范围")
        range_layout = QVBoxLayout(range_group)
        range_layout.addWidget(QLabel("输入页码 (如 1-3,5,7-10):"))
        self._range_input = QLineEdit()
        self._range_input.setPlaceholderText("例: 1-3,5,7-10")
        self._range_input.textChanged.connect(self._on_range_changed)
        range_layout.addWidget(self._range_input)
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: red; font-size: 11px;")
        self._error_label.setWordWrap(True)
        range_layout.addWidget(self._error_label)
        right_layout.addWidget(range_group)

        # 选择操作
        select_layout = QHBoxLayout()
        self._select_all_btn = QPushButton("全选")
        self._select_all_btn.clicked.connect(self._select_all)
        self._deselect_btn = QPushButton("取消全选")
        self._deselect_btn.clicked.connect(self._deselect_all)
        select_layout.addWidget(self._select_all_btn)
        select_layout.addWidget(self._deselect_btn)
        right_layout.addLayout(select_layout)

        # 选中状态
        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet("font-size: 13px; color: #333;")
        right_layout.addWidget(self._status_label)

        right_layout.addStretch()

        # 切分按钮
        self._split_btn = QPushButton("切分并保存")
        self._split_btn.setMinimumHeight(40)
        self._split_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #ccc; }
        """)
        self._split_btn.clicked.connect(self._split)
        self._split_btn.setEnabled(False)
        right_layout.addWidget(self._split_btn)

        main_layout.addWidget(right_panel)

    @Slot()
    def _load_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 PDF 文件", "", "PDF 文件 (*.pdf)"
        )
        if not path:
            return

        self._pdf_path = path
        self._range_input.clear()
        self._error_label.clear()

        import fitz
        try:
            doc = fitz.open(path)
            self._page_count = doc.page_count
            doc.close()
        except Exception:
            QMessageBox.warning(self, "错误", "无法打开该 PDF 文件")
            return

        name = os.path.basename(path)
        self._file_label.setText(f"{name}\n共 {self._page_count} 页")
        self._split_btn.setEnabled(True)

        self._grid.load_pdf(path)
        self._update_status()

    @Slot(str)
    def _on_range_changed(self, text: str):
        if self._updating_from_code:
            return
        if not self._pdf_path:
            return
        if not text.strip():
            self._error_label.clear()
            self._grid.deselect_all()
            self._update_status()
            return

        indices, errors = parse_page_ranges(text, self._page_count)
        if errors:
            self._error_label.setText("\n".join(errors))
        else:
            self._error_label.clear()

        self._updating_from_code = True
        self._grid.set_selected_pages(indices)
        self._updating_from_code = False
        self._update_status()

    @Slot()
    def _select_all(self):
        if not self._pdf_path:
            return
        self._grid.select_all()
        self._sync_range_input()

    @Slot()
    def _deselect_all(self):
        if not self._pdf_path:
            return
        self._grid.deselect_all()
        self._sync_range_input()

    def _sync_range_input(self):
        indices = self._grid.get_selected_pages()
        self._updating_from_code = True
        self._range_input.setText(indices_to_range_text(indices))
        self._updating_from_code = False
        self._update_status()

    def _on_grid_selection_changed(self):
        if not self._updating_from_code:
            self._sync_range_input()

    def _update_status(self):
        selected = len(self._grid.get_selected_pages())
        total = self._grid.page_count
        self._status_label.setText(f"已选: {selected} / {total} 页")

    @Slot()
    def _split(self):
        indices = self._grid.get_selected_pages()
        if not indices:
            QMessageBox.warning(self, "提示", "请至少选择一页")
            return

        default_name = os.path.splitext(os.path.basename(self._pdf_path))[0] + "_split.pdf"
        output_path, _ = QFileDialog.getSaveFileName(
            self, "保存切分后的 PDF", default_name, "PDF 文件 (*.pdf)"
        )
        if not output_path:
            return

        try:
            count = PdfEngine.split(self._pdf_path, indices, output_path)
            QMessageBox.information(
                self, "成功", f"切分完成，共 {count} 页\n保存至: {output_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "切分失败", str(e))
