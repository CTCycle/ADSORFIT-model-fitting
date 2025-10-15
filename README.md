# ADSORFIT: Automated Adsorption Model Fitting

## 1. Project Overview
ADSORFIT is a powerful yet simple tool designed to facilitate adsorption modeling for researchers. It automates experimental data fitting using theoretical adsorption models, enabling accurate extraction of adsorption constants and saturation uptakes from your adsorption isotherms. The core functionality revolves around minimizing the Least Squares Sum (LSS) discrepancy between observed data and model-predicted uptakes. This ensures that the derived model parameters reliably represent the true adsorption behavior under the given experimental conditions. The application now exposes its computation layer through a FastAPI backend and serves an intuitive user interface powered by Gradio, making it accessible to users of all experience levels.

## 2. Installation 
The installation process on Windows has been designed to be fully automated. To begin, simply run *start_on_windows.bat.* On its first execution, the installation procedure will execute with minimal user input required. The script will check if either Anaconda or Miniconda is installed and can be accessed from your system path. If neither is found, it will automatically download and install the latest Miniconda release from https://docs.anaconda.com/miniconda/. Following this step, the script will proceed with the installation of all necessary Python dependencies. Should you prefer to handle the installation process separately, you can run the standalone installer by running *setup/install_on_windows.bat*.  

**Important:** After installation, if the project folder is moved or its path is changed, the application will no longer function correctly. To fix this, you can either:

- Open the main menu, select *Setup and maintentance* and choose *Install project in editable mode*
- Manually run the following commands in the terminal, ensuring the project folder is set as the current working directory (CWD):

    `conda activate ADSORFIT`

    `pip install -e . --use-pep517` 

## 3. How to use
On Windows, run *start_on_windows.bat* to launch the main navigation menu and browse through the various options. Please note that some antivirus software, such as Avast, may flag or quarantine python.exe when called by the .bat file. If you encounter unusual behavior, consider adding an exception in your antivirus settings.

### 3.1 Navigation menu

**1) Run ADSORFIT UI:** Launch ADSORFIT to access the FastAPI backend and the Gradio-powered interface. When running locally (for example with `uvicorn ADSORFIT.app.app:app --reload` or via the Windows launcher), the backend listens on `http://127.0.0.1:8000` and the UI is exposed at `http://127.0.0.1:8000/ui`. The interface lets you upload an adsorption dataset, review automatic statistics, configure parameter bounds per model, and start the fitting procedure. Results are streamed back to the status panel as soon as the backend completes the computation.

**2) Setup and Maintenance:** execute optional commands such as *Install project into environment* to reinstall the project within your environment, *update project* to pull the last updates from github, and *remove logs* to remove all logs saved in *resources/logs*. 

**3) Exit:** close the program immediately 

### 3.2 Resources
This folder organizes data and results of the curve fitting operations, and by default all data is stored within an SQLite database. To visualize and interact with SQLite database files, we recommend downloading and installing the DB Browser for SQLite, available at: https://sqlitebrowser.org/dl/.


- **database:** adsorption isotherm data should be provided as a CSV file named *adsorption_data.csv*. If automatic column name detection is disabled, the file must include the following columns with these exact names and units: *experiment*, *temperature [K]*, *pressure [Pa]*, and *uptake [mol/g]*. On the other hand, if the option to automatically detect columns is selected, ADSORFIT will identify target columns based on keywords and string pattern matching. A template of the expected CSV format is available at *resources/templates/adsorption_data.csv*. Fitting results will be centrally stored within the main database *ADSORFIT_database.db*. 

- **logs:** log files are saved here

- **templates:** reference template files can be found here

### 4. Configuration
Each adsorption model can be configured in the **Model Configuration** tab where you can set an initial guess value for the adsorption model parameters,as well as boundaries for the minimun and maximum expected values.

**Environmental variables** are stored in the *app* folder (within the project folder). For security reasons, this file is typically not uploaded to GitHub. Instead, you must create this file manually by copying the template from *resources/templates/.env* and placing it in the *app* directory.

| Variable              | Description                                              |
|-----------------------|----------------------------------------------------------|
| FASTAPI_HOST          | Host address for the FastAPI server (default is 127.0.0.1) |
| FASTAPI_PORT          | Port to run the FastAPI server (default is 8000)          |
| RELOAD                | Enable auto-reload for development (true/false)           |
| ADSORFIT_API_URL      | Base URL used by the Gradio client to reach the backend   |

## 5. License
This project is licensed under the terms of the MIT license. See the LICENSE file for details.



