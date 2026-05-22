"""场景视图 — 插图 + 描述文本"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QTextEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


class SceneView(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("scene_view")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # 插图区
        self.image_label = QLabel()
        self.image_label.setFixedHeight(200)
        self.image_label.setMinimumHeight(140)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(
            "background-color: #0f0f23; border: 1px dashed #4a3f35; "
            "border-radius: 4px; color: #4a3f35; font-size: 14px;"
        )
        self._show_placeholder("场景插图")
        layout.addWidget(self.image_label)

        # 场景名称
        self.scene_title = QLabel("河畔镇")
        self.scene_title.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #c9a96e; padding: 2px 0;"
        )
        layout.addWidget(self.scene_title)

        # 描述文本
        self.desc_text = QTextEdit()
        self.desc_text.setReadOnly(True)
        self.desc_text.setStyleSheet(
            "background-color: #0f0f23; border: 1px solid #4a3f35; "
            "border-radius: 4px; font-size: 13px; padding: 8px;"
        )
        self.desc_text.setPlaceholderText("场景描述…")
        layout.addWidget(self.desc_text)

    def _show_placeholder(self, text: str) -> None:
        self.image_label.setText(f"[ {text} ]")

    def set_scene(self, scene_name: str, description: str) -> None:
        self.scene_title.setText(scene_name)
        self.desc_text.setPlainText(description)

    def set_image(self, path: str) -> None:
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            scaled = pixmap.scaledToWidth(
                self.image_label.width(), Qt.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)
        else:
            self._show_placeholder("图片未找到")

    def append_text(self, text: str) -> None:
        self.desc_text.append(text)
