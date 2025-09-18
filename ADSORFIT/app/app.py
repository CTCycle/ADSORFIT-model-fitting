from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from ADSORFIT.app.client.window import MainWindow, apply_style
from ADSORFIT.app.constants import UI_PATH
from ADSORFIT.app.logger import logger


###############################################################################
if __name__ == "__main__":
    try:
        qt_app = QApplication(sys.argv)
        apply_style(qt_app)
        main_window = MainWindow(UI_PATH)
        main_window.show()
        sys.exit(qt_app.exec())
    except Exception:
        logger.exception("ADSORFIT failed to start")
        sys.exit(1)
