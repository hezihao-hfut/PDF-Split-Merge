from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QTabWidget

from app.split_tab import SplitTab
from app.merge_tab import MergeTab


class MainWindow(QMainWindow):
    """主窗口：包含切分和整合两个标签页。"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF 切分与整合")
        self.setMinimumSize(900, 650)
        self.resize(1100, 750)

        tabs = QTabWidget()
        tabs.addTab(SplitTab(), "切分")
        tabs.addTab(MergeTab(), "整合")
        self.setCentralWidget(tabs)

        self.statusBar().showMessage("就绪")
