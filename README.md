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

- **Windows**: run `ADSORFIT/start_on_windows.bat` to launch both the FastAPI backend and the UI in a single step.
- **macOS/Linux**: activate your virtual environment, then start the web stack:

    ```bash
    uvicorn ADSORFIT.src.app:app --host 0.0.0.0 --port 8000
    ```

The interactive UI will be available at `http://127.0.0.1:7861`, while the API documentation can be viewed at `http://localhost:8000/docs`.

Once the UI is open:

Upload CSV or Excel adsorption datasets, inspect automatic profiling statistics, tune model bounds and iteration limits, and follow solver progress in real time. Model cards include enable toggles to restrict the run to relevant isotherms; at least one model must remain active before fitting can begin.

## 3.1 Setup and Maintenance
Execute `ADSORFIT/setup_and_maintenance.bat` to open the maintenance console. Available actions include:

- **Update project** – pull the latest revision from GitHub using the bundled Git client.
- **Remove logs** – clear accumulated log files stored in `ADSORFIT/resources/logs`

### 3.2 Resources
The `resources` directory aggregates inputs, outputs, and utilities used during fitting runs:

- **database:** Centralized SQLite storage for uploaded experiments and fitting results. Import CSV or Excel files that follow the template columns (experiment label, temperature in Kelvin, pressure in Pascal, and uptake in mol/g). A sample adsorption dataset is available at `ADSORFIT/resources/templates/adsorption_data.csv`, and external tools such as DB Browser for SQLite can be used for inspection.
- **logs:** Rolling backend and interface logs, useful for diagnosing solver behavior or API requests. The launcher offers a maintenance shortcut for clearing these files.
- **templates:** Assets such as the dataset template and environment variable scaffold referenced throughout this README.

### 4. Configuration
Each adsorption model can be configured in the **Model Configuration** area by adjusting parameter bounds, iteration ceilings, and persistence preferences. Bounds are validated to remain positive before fitting begins to avoid infeasible solver states.

Runtime options (host, port, reload mode, and API endpoint) are defined through environment variables. Copy the provided `.env` template from the templates collection, fill in the desired values, and place the finalized file at `ADSORFIT/setup/.env` before launching the server.

| Variable              | Description                                              |
|-----------------------|----------------------------------------------------------|
| FASTAPI_HOST          | Host address for the FastAPI server (default is 127.0.0.1) |
| FASTAPI_PORT          | Port to run the FastAPI server (default is 8000)          |
| RELOAD                | Enable auto-reload for development (true/false)           |
| ADSORFIT_API_URL      | Base URL used by the NiceGUI interface to reach the backend |

## 5. License
This project is licensed under the terms of the MIT license. See the LICENSE file for details.



