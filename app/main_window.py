from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QTabWidget

from app.split_tab import SplitTab
from app.merge_tab import MergeTab
from app.compress_tab import CompressTab


class MainWindow(QMainWindow):
    """主窗口：包含切分、整合和压缩三个标签页。"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF 切分与整合")
        self.setMinimumSize(900, 650)
        self.resize(1100, 750)

        tabs = QTabWidget()
        tabs.addTab(SplitTab(), "切分")
        tabs.addTab(MergeTab(), "整合")
        tabs.addTab(CompressTab(), "压缩")
        self.setCentralWidget(tabs)

        self.statusBar().showMessage("就绪")
