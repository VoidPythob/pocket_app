import argparse
import sys

from PyQt6.QtWidgets import QApplication

from pocket_app.config import init_config
from pocket_app.resources import load_app_font
from pocket_app.views import MainWindow


def parse_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "-c",
        "--config",
        dest="config_path",
        help="Path to config.json",
    )
    return parser.parse_known_args(argv[1:])


if __name__ == "__main__":
    args, qt_args = parse_args(sys.argv)
    init_config(args.config_path)

    app = QApplication([sys.argv[0], *qt_args])
    app.setFont(load_app_font())
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
