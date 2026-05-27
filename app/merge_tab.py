import os

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QListWidgetItem, QSizePolicy,
)

from app.widgets.drag_list_widget import DragListWidget
from app.widgets.pdf_list_item import PdfListItem
from app.core.pdf_engine import PdfEngine
from app.utils.page_range_parser import parse_page_ranges


class MergeTab(QWidget):
    """PDF 整合页：文件列表（支持拖拽排序）+ 控制面板。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._files: list[dict] = []  # [{"path": ..., "pages": int, "range": str}, ...]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 顶部按钮
        btn_layout = QHBoxLayout()
        self._add_btn = QPushButton("添加 PDF")
        self._add_btn.clicked.connect(self._add_files)
        btn_layout.addWidget(self._add_btn)

        self._remove_btn = QPushButton("移除选中")
        self._remove_btn.clicked.connect(self._remove_selected)
        btn_layout.addWidget(self._remove_btn)

        self._clear_btn = QPushButton("清空列表")
        self._clear_btn.clicked.connect(self._clear_list)
        btn_layout.addWidget(self._clear_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 提示
        hint = QLabel("拖拽列表项可调整顺序")
        hint.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(hint)

        # 列表
        self._list_widget = DragListWidget()
        self._list_widget.model().rowsMoved.connect(self._on_rows_moved)
        layout.addWidget(self._list_widget, stretch=1)

        # 统计信息
        self._stats_label = QLabel("共 0 个文件，0 页")
        self._stats_label.setAlignment(Qt.AlignCenter)
        self._stats_label.setStyleSheet("font-size: 13px; color: #333;")
        layout.addWidget(self._stats_label)

        # 合并按钮
        self._merge_btn = QPushButton("合并并保存")
        self._merge_btn.setMinimumHeight(40)
        self._merge_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #388E3C; }
            QPushButton:disabled { background-color: #ccc; }
        """)
        self._merge_btn.clicked.connect(self._merge)
        self._merge_btn.setEnabled(False)
        layout.addWidget(self._merge_btn)

    @Slot()
    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择 PDF 文件", "", "PDF 文件 (*.pdf)"
        )
        if not paths:
            return

        for path in paths:
            try:
                pages = PdfEngine.get_page_count(path)
            except Exception:
                QMessageBox.warning(self, "警告", f"无法读取: {os.path.basename(path)}")
                continue
            self._files.append({"path": path, "pages": pages, "range": ""})

        self._refresh_list()

    @Slot()
    def _remove_selected(self):
        row = self._list_widget.currentRow()
        if row < 0:
            return
        self._files.pop(row)
        self._refresh_list()

    @Slot()
    def _clear_list(self):
        self._files.clear()
        self._refresh_list()

    def _refresh_list(self):
        self._list_widget.clear()
        for i, f in enumerate(self._files):
            item = QListWidgetItem()
            widget = PdfListItem(i, f["path"], f["pages"])
            widget.remove_clicked.connect(self._on_remove_item)
            widget.page_range_changed.connect(self._on_page_range_changed)
            if f["range"]:
                widget._range_input.setText(f["range"])
            item.setSizeHint(widget.sizeHint())
            self._list_widget.addItem(item)
            self._list_widget.setItemWidget(item, widget)

        self._update_stats()
        self._merge_btn.setEnabled(len(self._files) >= 2)

    def _update_stats(self):
        total_pages = sum(f["pages"] for f in self._files)
        selected = 0
        for f in self._files:
            if f["range"].strip():
                indices, errors = parse_page_ranges(f["range"], f["pages"])
                selected += len(indices) if not errors else f["pages"]
            else:
                selected += f["pages"]
        self._stats_label.setText(
            f"共 {len(self._files)} 个文件，{total_pages} 页（将合并 {selected} 页）"
        )

    def _on_remove_item(self, index: int):
        if 0 <= index < len(self._files):
            self._files.pop(index)
            self._refresh_list()

    def _on_page_range_changed(self, index: int, text: str):
        if 0 <= index < len(self._files):
            self._files[index]["range"] = text
            self._update_stats()

    @Slot()
    def _on_rows_moved(self):
        """拖拽排序后同步底层数据。"""
        new_order = []
        for i in range(self._list_widget.count()):
            widget = self._list_widget.itemWidget(self._list_widget.item(i))
            if widget:
                new_order.append({
                    "path": widget.file_path,
                    "pages": widget.page_count,
                    "range": widget.page_range_text,
                })
        self._files = new_order
        self._refresh_list()

    @Slot()
    def _merge(self):
        if len(self._files) < 2:
            QMessageBox.warning(self, "提示", "至少需要两个 PDF 文件")
            return

        # 验证所有页码范围
        page_ranges = []
        for f in self._files:
            if f["range"].strip():
                indices, errors = parse_page_ranges(f["range"], f["pages"])
                if errors:
                    QMessageBox.warning(
                        self, "页码错误",
                        f"{os.path.basename(f['path'])}:\n" + "\n".join(errors)
                    )
                    return
                page_ranges.append(indices)
            else:
                page_ranges.append(None)

        output_path, _ = QFileDialog.getSaveFileName(
            self, "保存合并后的 PDF", "merged.pdf", "PDF 文件 (*.pdf)"
        )
        if not output_path:
            return

        paths = [f["path"] for f in self._files]
        try:
            count = PdfEngine.merge(paths, output_path, page_ranges)
            QMessageBox.information(
                self, "成功", f"合并完成，共 {count} 页\n保存至: {output_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "合并失败", str(e))
