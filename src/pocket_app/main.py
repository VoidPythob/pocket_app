import sys

from PyQt6.QtWidgets import QApplication

from pocket_app.views import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
