# ADSORFIT: Automated Adsorption Model Fitting

## 1. Project Overview
ADSORFIT accelerates adsorption-model research by combining automated curve fitting, visual analytics, and experiment management in a single workflow. A shared FastAPI service and NiceGUI interface coordinate dataset ingestion, parameter exploration, and solver execution so interactive users and scripted integrations access the same capabilities. The fitting engine minimizes the least-squares distance between measured uptake profiles and the predictions of classical adsorption models, enabling quick comparison of hypotheses, sensitivity studies, and archiving of the best-performing solutions for future review.

## 2. Installation
### 2.1 Prerequisites
- Python 3.12
- A recent version of `pip`
- Recommended: a virtual environment manager such as `venv`, Conda, or Hatch

### 2.2 Standard setup
1. Create and activate a Python 3.12 environment.
2. Upgrade `pip` and install project dependencies from the repository root with `pip install --upgrade pip` followed by `pip install -e . --use-pep517`.
3. (Optional) If you plan to run the test suite, install the extra tooling with `pip install -e .[dev]`.

### 2.3 Windows launcher
Windows users can still rely on the bundled automation scripts. Launch `start_on_windows.bat` to install dependencies, configure the virtual environment, and open the application menu. The first run can take a few minutes while Miniconda and project requirements are prepared.

If the project directory moves after installation, rerun the menu option **Install project in editable mode** or repeat step 2 from the standard setup while the environment is active.

## 3. How to use
### 3.0 Launching the application
- Local development: start the backend with `uvicorn ADSORFIT.app.app:app --reload` to enable live reloading. The UI is available at `http://127.0.0.1:8000/ui` and FastAPI's interactive docs remain accessible at `/docs`.
- Production-like sessions: run `uvicorn ADSORFIT.app.app:app --host 0.0.0.0 --port 8000` and visit the `/ui` endpoint in a browser of your choice. The API documentation is mirrored at `/docs` for automated workflows.
- Windows launcher: from the navigation menu, choose **Run ADSORFIT UI**. Antivirus tools may prompt for confirmation while the bundled interpreter starts; whitelist the launcher if necessary.

### 3.1 Navigation menu

**1) Run ADSORFIT UI:** Starts the API and the NiceGUI interface. Upload CSV or Excel adsorption datasets, inspect automatic profiling statistics, tune model bounds and iteration limits, and follow solver progress in real time. Model cards include enable toggles to restrict the run to relevant isotherms; at least one model must remain active before fitting can begin.

**2) Setup and Maintenance:** Provides shortcuts to reinstall ADSORFIT into the active environment, update dependencies from version control, or rotate stored logs without leaving the launcher.

**3) Exit:** Closes the launcher.

### 3.2 Resources
The `resources` directory aggregates inputs, outputs, and utilities used during fitting runs:

- **database:** Centralized SQLite storage for uploaded experiments and fitting results. Import CSV or Excel files that follow the template columns (experiment label, temperature in Kelvin, pressure in Pascal, and uptake in mol/g). A sample adsorption dataset is available at `ADSORFIT/resources/templates/adsorption_data.csv`, and external tools such as DB Browser for SQLite can be used for inspection.
- **logs:** Rolling backend and interface logs, useful for diagnosing solver behavior or API requests. The launcher offers a maintenance shortcut for clearing these files.
- **templates:** Assets such as the dataset template and environment variable scaffold referenced throughout this README.

### 4. Configuration
Each adsorption model can be configured in the **Model Configuration** area by adjusting parameter bounds, iteration ceilings, and persistence preferences. Bounds are validated to remain positive before fitting begins to avoid infeasible solver states.

Runtime options (host, port, reload mode, and API endpoint) are defined through environment variables. Copy the provided `.env` template from the templates collection, fill in the desired values, and place the finalized file at `ADSORFIT/app/.env` before launching the server.

| Variable              | Description                                              |
|-----------------------|----------------------------------------------------------|
| FASTAPI_HOST          | Host address for the FastAPI server (default is 127.0.0.1) |
| FASTAPI_PORT          | Port to run the FastAPI server (default is 8000)          |
| RELOAD                | Enable auto-reload for development (true/false)           |
| ADSORFIT_API_URL      | Base URL used by the NiceGUI interface to reach the backend |

## 5. License
This project is licensed under the terms of the MIT license. See the LICENSE file for details.



