import sys
from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

# [SETTING WARNINGS]
import warnings
warnings.simplefilter(action='ignore', category=Warning)

# [IMPORT CUSTOM MODULES]
from ADSORFIT.app.client.window import MainWindow, apply_style
from ADSORFIT.app.constants import UI_PATH
from ADSORFIT.app.logger import logger


# [RUN MAIN]
###############################################################################
if __name__ == "__main__":  
    app = QApplication(sys.argv)
    app = apply_style(app)
    main_window = MainWindow(UI_PATH)
    main_window.show()
    sys.exit(app.exec())


   
