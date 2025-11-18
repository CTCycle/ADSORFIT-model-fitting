from __future__ import annotations

from os.path import abspath, join

# [PATHS]
###############################################################################
ROOT_DIR = abspath(join(__file__, "../../../.."))
PROJECT_DIR = join(ROOT_DIR, "ADSORFIT")
SETTING_PATH = join(PROJECT_DIR, "setup", "settings")
RESOURCES_PATH = join(PROJECT_DIR, "resources")
DATA_PATH = join(RESOURCES_PATH, "database")
CONFIG_PATH = join(RESOURCES_PATH, "configurations")
LOGS_PATH = join(RESOURCES_PATH, "logs")
TEMPLATES_PATH = join(RESOURCES_PATH, "templates")
CONFIGURATION_FILE = join(SETTING_PATH, "configurations.json")
ENV_FILE_PATH = join(SETTING_PATH, ".env")
DATABASE_FILENAME = "database.db"


###############################################################################
MODELS_LIST = [
    "Langmuir",
    "Sips",
    "Freundlich",
    "Temkin",
    "Toth",
    "Dubinin-Radushkevich",
    "Dual-Site Langmuir",
    "Redlich-Peterson",
    "Jovanovic",
    "BET",
    "Henry",
    "Koble-Corrigan",
]

MODEL_PARAMETER_DEFAULTS: dict[str, dict[str, tuple[float, float]]] = {
    "Langmuir": {
        "k": (1e-06, 10.0),
        "qsat": (0.0, 100.0),
    },
    "Sips": {
        "k": (1e-06, 10.0),
        "qsat": (0.0, 100.0),
        "exponent": (0.1, 10.0),
    },
    "Freundlich": {
        "k": (1e-06, 10.0),
        "exponent": (0.1, 10.0),
    },
    "Temkin": {
        "k": (1e-06, 10.0),
        "beta": (0.1, 10.0),
    },
}

DEFAULT_DATASET_COLUMN_MAPPING = {
    "experiment": "experiment",
    "temperature": "temperature [K]",
    "pressure": "pressure [Pa]",
    "uptake": "uptake [mol/g]",
}

DATASET_FALLBACK_DELIMITERS = (";", "\t", "|")

FITTING_MODEL_NAMES = ("LANGMUIR", "SIPS", "FREUNDLICH", "TEMKIN")
