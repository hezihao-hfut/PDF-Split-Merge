import fitz
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage, QPixmap, Qt


class ThumbnailWorker(QThread):
    """在后台线程中渲染 PDF 页面缩略图。"""

    page_ready = Signal(int, QPixmap)  # (page_index, pixmap)
    error = Signal(str)

    def __init__(self, pdf_path: str, thumb_width: int = 150, thumb_height: int = 200):
        super().__init__()
        self.pdf_path = pdf_path
        self.thumb_width = thumb_width
        self.thumb_height = thumb_height

    def run(self):
        doc = None
        try:
            doc = fitz.open(self.pdf_path)
            for i in range(doc.page_count):
                if self.isInterruptionRequested():
                    return
                page = doc[i]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                qimg = qimg.copy()  # 必须复制，pix.samples 会被释放
                pixmap = QPixmap.fromImage(qimg)
                pixmap = pixmap.scaled(
                    self.thumb_width, self.thumb_height,
                    Qt.KeepAspectRatio, Qt.SmoothTransformation,
                )
                self.page_ready.emit(i, pixmap)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            if doc:
                doc.close()
