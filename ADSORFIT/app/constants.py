from __future__ import annotations

from os.path import abspath, join

# [PATHS]
###############################################################################
ROOT_DIR = abspath(join(__file__, "../../.."))
PROJECT_DIR = join(ROOT_DIR, "ADSORFIT")
SETUP_PATH = join(ROOT_DIR, "setup")
RESOURCES_PATH = join(PROJECT_DIR, "resources")
DATA_PATH = join(RESOURCES_PATH, "database")
CONFIG_PATH = join(RESOURCES_PATH, "configurations")
LOGS_PATH = join(RESOURCES_PATH, "logs")
TEMPLATES_PATH = join(RESOURCES_PATH, "templates")

# [FILENAMES]
###############################################################################
DATASET_PATH = join(DATA_PATH, "adsorption_data.csv")
RESULTS_PATH = join(DATA_PATH, "adsorption_model_fit.csv")

# [UI LAYOUT PATH]
###############################################################################
UI_PATH = join(PROJECT_DIR, "app", "assets", "window_layout.ui")
