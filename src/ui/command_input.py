"""命令输入 — 聊天风格 + 发送按钮"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QKeyEvent


class CommandInput(QWidget):
    command_entered = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # 输入框
        self.input = QLineEdit()
        self.input.setPlaceholderText("💬 输入指令或与角色对话…（帮助 / 探索 / 前往 / 对话）")
        self.input.setStyleSheet(
            "QLineEdit {"
            "  background: rgba(15, 15, 35, 0.9);"
            "  color: #e8d5b0;"
            "  border: 2px solid #4a3f35;"
            "  border-radius: 20px;"
            "  padding: 10px 16px;"
            "  font-size: 15px;"
            "}"
            "QLineEdit:focus { border-color: #c9a96e; }"
        )
        self.input.returnPressed.connect(self._on_send)
        layout.addWidget(self.input, stretch=1)

        # 发送按钮
        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedSize(60, 36)
        self.send_btn.setStyleSheet(
            "QPushButton {"
            "  background: #c9a96e; color: #1a1a2e;"
            "  border: none; border-radius: 18px;"
            "  font-size: 13px; font-weight: bold;"
            "}"
            "QPushButton:hover { background: #d4b87a; }"
            "QPushButton:pressed { background: #a08050; }"
        )
        self.send_btn.clicked.connect(self._on_send)
        layout.addWidget(self.send_btn)

        self._history: list[str] = []
        self._history_index: int = -1

    def _on_send(self) -> None:
        text = self.input.text().strip()
        if text:
            self._history.append(text)
            self._history_index = len(self._history)
            self.command_entered.emit(text)
            self.input.clear()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Up:
            if self._history and self._history_index > 0:
                self._history_index -= 1
                self.input.setText(self._history[self._history_index])
            return
        if event.key() == Qt.Key_Down:
            if self._history_index < len(self._history) - 1:
                self._history_index += 1
                self.input.setText(self._history[self._history_index])
            else:
                self._history_index = len(self._history)
                self.input.clear()
            return
        super().keyPressEvent(event)

    def set_placeholder(self, text: str) -> None:
        self.input.setPlaceholderText(text)

    def focus(self) -> None:
        self.input.setFocus()
