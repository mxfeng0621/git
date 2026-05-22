"""圆形头像组件 — AI插图预留"""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QPainter, QBrush, QColor, QPainterPath


RACE_ICONS = {
    "human": "👤", "elf": "🧝", "dwarf": "🧔", "halfling": "🧒",
}

CLASS_COLORS = {
    "warrior": "#c0392b", "mage": "#2980b9", "rogue": "#27ae60",
    "cleric": "#f39c12", "ranger": "#2ecc71",
}


class PortraitWidget(QWidget):
    """圆形头像占位，预留AI生成接口"""

    def __init__(self, size: int = 56, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size + 4, size + 4)
        self._pixmap: QPixmap | None = None
        self._placeholder_text: str = "?"

    def set_placeholder(self, race_id: str, class_id: str) -> None:
        """用种族图标+职业颜色填充占位"""
        icon = RACE_ICONS.get(race_id, "?")
        color = CLASS_COLORS.get(class_id, "#888")
        self._placeholder_text = icon
        self.setStyleSheet(
            f"PortraitWidget {{ background: {color}; border: 2px solid #c9a96e; "
            f"border-radius: {self._size // 2 + 2}px; }}"
        )
        self._pixmap = None
        self.update()

    def set_image(self, path: str) -> None:
        """加载本地图片"""
        self._pixmap = QPixmap(path)
        if self._pixmap.isNull():
            self._pixmap = None
        self.update()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QBrush, QColor, QPainterPath, QFont
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        r = 2
        w = self._size
        path = QPainterPath()
        path.addEllipse(r, r, w, w)
        painter.setClipPath(path)

        if self._pixmap:
            painter.drawPixmap(r, r, w, w, self._pixmap)
        else:
            painter.setPen(Qt.NoPen)
            painter.drawPath(path)
            painter.setPen(QColor("#d4c5a9"))
            font = QFont("Microsoft YaHei", w // 3)
            painter.setFont(font)
            painter.drawText(r, r, w, w, Qt.AlignCenter, self._placeholder_text)

        # 边框
        painter.setClipping(False)
        painter.setPen(QColor("#c9a96e"))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(r, r, w, w)
        painter.end()
