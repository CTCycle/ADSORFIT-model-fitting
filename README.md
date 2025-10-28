# ADSORFIT: Automated Adsorption Model Fitting

ADSORFIT combines a FastAPI backend, a NiceGUI-powered interface, and classic adsorption models to streamline parameter fitting for gas adsorption experiments. Researchers can upload uptake measurements, compare model families side by side, and archive the best solutions without leaving the browser.

## Table of Contents
- [Key Features](#key-features)
- [Architecture Overview](#architecture-overview)
- [Repository Layout](#repository-layout)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Using uv (recommended)](#using-uv-recommended)
  - [Using pip](#using-pip)
- [Running the Application](#running-the-application)
  - [Backend and UI](#backend-and-ui)
  - [Working with Datasets](#working-with-datasets)
  - [Configuration](#configuration)
- [Windows Automation Scripts](#windows-automation-scripts)
  - [`start_on_windows.bat`](#start_on_windowsbat)
  - [`setup_and_maintenance.bat`](#setup_and_maintenancebat)
- [Development Tips](#development-tips)
- [License](#license)

## Key Features
- **End-to-end fitting workflow**: Upload adsorption datasets (CSV or Excel), configure parameter bounds, select models, and launch fittings directly from the NiceGUI dashboard.
- **Multiple adsorption models**: Langmuir, Sips, Freundlich, and Temkin models ship with editable default bounds and iteration limits so that experiments start with sensible values.
- **Shared FastAPI backend**: REST endpoints exposed under `/api` allow programmatic access to dataset ingestion and fitting routines, while the interactive UI lives at `/ui`.
- **Persistent storage**: Results and metadata are stored in the SQLite database under `ADSORFIT/resources/database`, with log files and templates collocated inside `ADSORFIT/resources` for easy inspection.
- **Configurable runtime**: Environment variables and JSON configuration files allow you to tune server settings, defaults, and experiment metadata columns without modifying code.

## Architecture Overview
The backend lives in `ADSORFIT/app` and defines three main layers:

1. **API (`ADSORFIT/app/api`)** – FastAPI routers expose dataset, configuration, and fitting endpoints.
2. **Client (`ADSORFIT/app/client`)** – NiceGUI components (see `interface.py`) render the single-page application, handle uploads, and trigger fitting jobs via the API client controllers.
3. **Utilities (`ADSORFIT/app/utils`)** – Data preparation, model definitions, and optimization helpers used by both the API and interface.

The entrypoint for Uvicorn is `ADSORFIT.app.app:app`, which registers the API router and renders the UI. Configuration values are loaded through `ADSORFIT/app/variables.py`, which reads `ADSORFIT/app/.env` when present.

## Repository Layout
```
ADSORFIT-model-fitting/
├── ADSORFIT/
│   ├── app/                # FastAPI + NiceGUI application
│   ├── resources/          # Database, logs, and dataset templates
│   ├── setup/              # Bootstrap assets, scripts, and embedded Python runtime
│   ├── setup_and_maintenance.bat
│   └── start_on_windows.bat
├── pyproject.toml          # Project metadata and dependency list
└── README.md
```

## Requirements
- Python 3.12
- `uv` (for the recommended workflow) or `pip`
- Optional: a virtual environment manager such as `venv`, Conda, or Hatch

## Installation
### Using uv (recommended)
`uv` handles dependency resolution quickly and is already bundled with the Windows launcher. To use it on macOS or Linux:

1. Install `uv` by following the [official instructions](https://docs.astral.sh/uv/getting-started/installation/).
2. Clone the repository and change into its root directory.
3. Create an isolated environment and install dependencies:
   ```bash
   uv sync
   ```
   This command respects `pyproject.toml`, creating a virtual environment (typically in `.venv/`) with all runtime dependencies.

Activate the environment when your shell session does not do so automatically:
```bash
source .venv/bin/activate  # Linux/macOS
.\.venv\Scripts\activate  # Windows PowerShell
```

### Using pip
If you prefer a manual setup:

1. Create and activate a Python 3.12 environment using `python -m venv .venv` (or your preferred manager).
2. Upgrade `pip` and install the project in editable mode:
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -e . --use-pep517
   ```
3. (Optional) Install development extras if you plan to run formatting or linting tools:
   ```bash
   python -m pip install -e .[dev]
   ```

## Running the Application
### Backend and UI
Once dependencies are installed and the environment is active, launch the FastAPI server with Uvicorn:
```bash
uvicorn ADSORFIT.app.app:app --reload
```
The NiceGUI interface is served at `http://127.0.0.1:8000/ui` and the FastAPI docs are available at `http://127.0.0.1:8000/docs`. Omit `--reload` for production-like sessions or expose the service with `--host 0.0.0.0 --port 8000`.

### Working with Datasets
- Supported formats: `.csv` and `.xlsx`.
- Upload files via the "Load dataset" control in the UI. The interface renders summary statistics before fitting begins.
- Column names default to `experiment`, `temperature [K]`, `pressure [Pa]`, and `uptake [mol/g]`. Adjust them in the configuration area if your data uses different headers.
- A template file is located at `ADSORFIT/resources/templates/adsorption_data.csv` for quick experimentation.
- Results are persisted in the SQLite database inside `ADSORFIT/resources/database` and accompanied by logs under `ADSORFIT/resources/logs`.

### Configuration
1. **Environment variables** – Create `ADSORFIT/app/.env` to override the defaults bundled with the application. The Windows launcher also looks for overrides in `ADSORFIT/setup/.env`. Define values such as:
   - `FASTAPI_HOST` (default `127.0.0.1`)
   - `FASTAPI_PORT` (default `8000`)
   - `RELOAD` (`true` or `false`)
   - `ADSORFIT_API_URL` (base URL that the UI uses to reach the backend)
2. **Model defaults** – Use the UI to tweak parameter bounds and iteration limits per model. Configurations can be exported and reloaded as JSON through the interface controls (`ADSORFIT/app/configuration.py`).

## Windows Automation Scripts
Two batch files in `ADSORFIT/` simplify Windows usage by bundling an embeddable Python distribution and Astral's `uv`.

### `start_on_windows.bat`
This script is the main launcher and performs the following steps:
1. **Bootstraps Python 3.12** – Downloads the embeddable package from python.org if it is not already cached in `ADSORFIT/setup/python` and patches it to load site-packages.
2. **Installs `uv`** – Fetches the latest portable release for your architecture and drops `uv.exe` inside `ADSORFIT/setup/uv`.
3. **Installs project dependencies** – Runs `uv sync` against `pyproject.toml`, preferring the bundled Python runtime. If installation fails it retries with a managed interpreter.
4. **Cleans the cache** – Clears the local `uv` cache directory to minimize disk usage.
5. **Loads environment overrides** – Reads `ADSORFIT/setup/.env` when present to configure host, port, and reload mode before launching.
6. **Starts the app** – Opens the browser at `/ui` and executes `uv run --python python.exe uvicorn ADSORFIT.app.app:app ...` so that the interface and API are ready immediately.

Re-run `start_on_windows.bat` whenever dependencies change or you move the project directory. The script creates an `.is_installed` marker after a successful install, which enables a fast path for subsequent launches.

### `setup_and_maintenance.bat`
Use this optional menu for manual maintenance:
1. **Enable root path imports** – Executes `pip install -e . --use-pep517` inside the managed Python environment to refresh editable installs.
2. **Update project** – Runs `ADSORFIT/setup/scripts/update_project.py` for custom update logic (for example, pulling from version control).
3. **Remove logs** – Deletes all `.log` files inside `ADSORFIT/resources/logs` to free disk space.

Launch the menu whenever you need to reinstall the project after switching branches, update dependencies, or clear accumulated log files.

## Development Tips
- Run `uvicorn` with `--reload` for automatic code reloading during development.
- Use the NiceGUI interface to verify parameter presets, model toggles, and upload flows.
- Check `ADSORFIT/resources/logs` for troubleshooting; logs are rotated by the Windows maintenance menu.
- Ensure new datasets follow the template structure so that automatic column detection works reliably.

## License
This project is distributed under the MIT License. Refer to [`LICENSE`](LICENSE) for full details.
