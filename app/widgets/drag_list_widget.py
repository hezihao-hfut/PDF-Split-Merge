from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget, QListWidgetItem


class DragListWidget(QListWidget):
    """支持拖拽排序的列表控件。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setSpacing(2)
        self.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #fafafa;
            }
            QListWidget::item {
                padding: 2px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)
