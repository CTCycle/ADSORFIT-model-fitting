from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from ADSORFIT.app.constants import PROJECT_DIR
from ADSORFIT.app.logger import logger


###############################################################################
class EnvironmentVariables:
    def __init__(self) -> None:
        self.env_path = Path(PROJECT_DIR) / "app" / ".env"
        if self.env_path.exists():
            load_dotenv(self.env_path)
        else:
            logger.info(
                "Environment file not found at %s; default values will be used",
                self.env_path,
            )

    # -------------------------------------------------------------------------
    def get(self, key: str, default: str | None = None) -> str | None:
        return os.getenv(key, default)
