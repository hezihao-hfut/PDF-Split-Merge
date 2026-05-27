import os

from PySide6.QtCore import Qt, Slot, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QProgressBar,
)

from app.core.pdf_engine import PdfEngine


class _CompressWorker(QThread):
    """后台线程执行压缩，避免阻塞 UI。"""

    finished = Signal(str)  # output_path
    error = Signal(str)
    progress = Signal(int, int)  # (current_page, total_pages)

    def __init__(self, input_path: str, output_path: str, quality: int, parent=None):
        super().__init__(parent)
        self._input_path = input_path
        self._output_path = output_path
        self._quality = quality

    def run(self):
        try:
            PdfEngine.compress(
                self._input_path, self._output_path,
                quality=self._quality,
                progress_cb=lambda cur, total: self.progress.emit(cur, total),
            )
            self.finished.emit(self._output_path)
        except Exception as e:
            self.error.emit(str(e))


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


class CompressTab(QWidget):
    """PDF 压缩页：加载 PDF，选择压缩质量，压缩并保存。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._input_path: str | None = None
        self._worker: _CompressWorker | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignTop)

        # 文件选择
        file_layout = QHBoxLayout()
        self._load_btn = QPushButton("选择 PDF 文件")
        self._load_btn.clicked.connect(self._load_pdf)
        file_layout.addWidget(self._load_btn)
        self._file_label = QLabel("未选择文件")
        self._file_label.setStyleSheet("color: #666; font-size: 13px;")
        file_layout.addWidget(self._file_label, stretch=1)
        layout.addLayout(file_layout)

        # 原始大小
        self._size_label = QLabel("")
        self._size_label.setStyleSheet("font-size: 14px; color: #333;")
        layout.addWidget(self._size_label)

        # 压缩质量选择
        quality_label = QLabel("压缩质量:")
        quality_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(quality_label)

        quality_layout = QHBoxLayout()
        self._quality_btns = []
        for text, value, tooltip in [
            ("低 (最小体积)", 0, "最大压缩，可能降低图片质量"),
            ("中 (推荐)", 1, "平衡体积与质量"),
            ("高 (最佳质量)", 2, "轻微压缩，保持原始质量"),
        ]:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setToolTip(tooltip)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 8px 16px;
                    border: 2px solid #ccc;
                    border-radius: 4px;
                    font-size: 13px;
                }
                QPushButton:checked {
                    border-color: #2196F3;
                    background-color: #e3f2fd;
                }
            """)
            btn.clicked.connect(lambda checked, v=value: self._set_quality(v))
            quality_layout.addWidget(btn)
            self._quality_btns.append((btn, value))
        layout.addLayout(quality_layout)

        self._quality = 1  # 默认中等
        self._quality_btns[1][0].setChecked(True)

        # 进度条
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        self._progress_bar.setTextVisible(True)
        layout.addWidget(self._progress_bar)

        # 状态
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self._status_label)

        layout.addStretch()

        # 压缩按钮
        self._compress_btn = QPushButton("压缩并保存")
        self._compress_btn.setMinimumHeight(40)
        self._compress_btn.setEnabled(False)
        self._compress_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #F57C00; }
            QPushButton:disabled { background-color: #ccc; }
        """)
        self._compress_btn.clicked.connect(self._compress)
        layout.addWidget(self._compress_btn)

    def _set_quality(self, value: int):
        self._quality = value
        for btn, v in self._quality_btns:
            btn.setChecked(v == value)

    @Slot()
    def _load_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 PDF 文件", "", "PDF 文件 (*.pdf)"
        )
        if not path:
            return

        self._input_path = path
        name = os.path.basename(path)
        size = os.path.getsize(path)
        self._file_label.setText(name)
        self._size_label.setText(f"原始大小: {_format_size(size)}")
        self._status_label.setText("")
        self._compress_btn.setEnabled(True)

    @Slot()
    def _compress(self):
        if not self._input_path:
            return

        default_name = os.path.splitext(os.path.basename(self._input_path))[0] + "_compressed.pdf"
        output_path, _ = QFileDialog.getSaveFileName(
            self, "保存压缩后的 PDF", default_name, "PDF 文件 (*.pdf)"
        )
        if not output_path:
            return

        self._compress_btn.setEnabled(False)
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)
        self._status_label.setText("正在压缩...")

        self._worker = _CompressWorker(self._input_path, output_path, self._quality)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, current: int, total: int):
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(current)
        self._progress_bar.setFormat(f"处理第 {current}/{total} 页")

    def _on_finished(self, output_path: str):
        self._progress_bar.setVisible(False)
        self._compress_btn.setEnabled(True)

        original_size = os.path.getsize(self._input_path)
        compressed_size = os.path.getsize(output_path)
        ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

        self._status_label.setText(
            f"压缩完成!  {_format_size(original_size)} → {_format_size(compressed_size)}"
            f"  (减小 {ratio:.1f}%)"
        )
        QMessageBox.information(
            self, "压缩完成",
            f"原始大小: {_format_size(original_size)}\n"
            f"压缩后: {_format_size(compressed_size)}\n"
            f"减小: {ratio:.1f}%\n\n"
            f"保存至: {output_path}"
        )

    def _on_error(self, msg: str):
        self._progress_bar.setVisible(False)
        self._compress_btn.setEnabled(True)
        self._status_label.setText(f"压缩失败: {msg}")
        QMessageBox.critical(self, "压缩失败", msg)
