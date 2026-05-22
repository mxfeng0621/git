"""消息日志面板"""

from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import QTextCursor

from utils.constants import MessageCategory


CATEGORY_COLORS = {
    MessageCategory.INFO: "#c0b090",
    MessageCategory.WARNING: "#e6a817",
    MessageCategory.DANGER: "#e63946",
    MessageCategory.LOOT: "#f0a500",
    MessageCategory.COMBAT: "#8ecae6",
    MessageCategory.SYSTEM: "#6c757d",
}


class LogPanel(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("你的冒险将从这里开始…")
        self.setMinimumHeight(100)
        self.setStyleSheet(
            "QTextEdit { background-color: #0f0f23; color: #c0b090; "
            "border: 1px solid #4a3f35; border-radius: 4px; "
            "font-family: 'Microsoft YaHei', 'SimHei', monospace; "
            "font-size: 13px; padding: 6px; }"
        )

    def log(self, text: str, category: MessageCategory = MessageCategory.INFO) -> None:
        color = CATEGORY_COLORS.get(category, "#c0b090")
        for line in text.split("\n"):
            self.append(f'<span style="color:{color}">{line}</span>')
        self._scroll_bottom()

    def log_system(self, text: str) -> None:
        self.log(text, MessageCategory.SYSTEM)

    def log_combat(self, text: str) -> None:
        self.log(text, MessageCategory.COMBAT)

    def log_danger(self, text: str) -> None:
        self.log(text, MessageCategory.DANGER)

    def log_loot(self, text: str) -> None:
        self.log(text, MessageCategory.LOOT)

    def log_command(self, text: str) -> None:
        self.append(f'<span style="color:#c9a96e;font-weight:bold">▸ {text}</span>')
        self._scroll_bottom()

    def _scroll_bottom(self) -> None:
        self.moveCursor(QTextCursor.End)
