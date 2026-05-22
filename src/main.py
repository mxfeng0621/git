"""龙焰传说 — 应用入口"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from app.main_window import MainWindow
from db.database import init_db


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("龙焰传说")

    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    init_db()
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
