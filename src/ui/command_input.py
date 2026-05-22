"""命令输入组件 — 带历史记录"""

from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import Qt


class CommandInput(QLineEdit):
    command_entered = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("输入指令…（帮助 / 探索 / 状态 / 背包）")
        self.setStyleSheet(
            "QLineEdit { background-color: #0f0f23; color: #e8d5b0; "
            "border: 2px solid #4a3f35; border-radius: 4px; "
            "padding: 8px 12px; font-size: 15px; "
            "selection-background-color: #c9a96e; selection-color: #1a1a2e; } "
            "QLineEdit:focus { border-color: #c9a96e; }"
        )
        self._history: list[str] = []
        self._history_index: int = -1

        self.returnPressed.connect(self._on_enter)

    def _on_enter(self) -> None:
        text = self.text().strip()
        if text:
            self._history.append(text)
            self._history_index = len(self._history)
            self.command_entered.emit(text)
            self.clear()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Up:
            if self._history and self._history_index > 0:
                self._history_index -= 1
                self.setText(self._history[self._history_index])
            return
        if event.key() == Qt.Key_Down:
            if self._history_index < len(self._history) - 1:
                self._history_index += 1
                self.setText(self._history[self._history_index])
            else:
                self._history_index = len(self._history)
                self.clear()
            return
        super().keyPressEvent(event)
