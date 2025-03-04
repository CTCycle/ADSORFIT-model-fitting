# ADSORFIT: Automated Adsorption Model Fitting

## 1. Project Overview
ADSORFIT is a powerful tool designed to simplify and enhance adsorption modeling for researchers. It automates the fitting of theoretical adsorption models to experimental isotherm data, enabling accurate extraction of key adsorption parameters such as adsorption constants and saturation uptakes. The core functionality focuses on minimizing the Least Squares Sum (LSS) discrepancy between observed data and model-predicted uptakes. This ensures that the derived model parameters reliably represent the true adsorption behavior under the given experimental conditions. ADSORFIT features an intuitive, user-friendly interface built with NiceGUI, making advanced adsorption modeling accessible to users of all experience levels.

## 2. Installation 
The installation process on Windows has been designed for simplicity and ease of use. To begin, simply run *start_on_windows.bat.* On its first execution, the installation procedure will automatically start with minimal user input required. The script will check if either Anaconda or Miniconda is installed on your system. If neither is found, it will automatically download and install the latest Miniconda release from https://docs.anaconda.com/miniconda/. After setting up Anaconda/Miniconda, the installation script will proceed with the installation of all necessary Python dependencies. If you'd prefer to handle the installation process separately, you can run the standalone installer by executing *setup/install_on_windows.bat*.  

**Important:** After installation, if the project folder is moved or its path is changed, the application will no longer function correctly. To fix this, you can either:

- Open the main menu, select *Setup and maintentance* and choose *Install project in editable mode*
- Manually run the following commands in the terminal, ensuring the project folder is set as the current working directory (CWD):

    `conda activate ADSORFIT`

    `pip install -e . --use-pep517` 

## 3. How to use
On Windows, run *start_on_windows.bat* to launch the main navigation menu and browse through the various options. Alternatively, you can launch the main app file running *python ADSORFIT/commons/main.py*. Please note that some antivirus software, such as Avast, may flag or quarantine python.exe when called by the .bat file. If you encounter unusual behavior, consider adding an exception for your Anaconda or Miniconda environments in your antivirus settings.

**Environmental variables** are stored in *resources/variables/.env*. For security reasons, this file is typically not uploaded to GitHub. Instead, you must create this file manually by copying the template from *resources/templates/.env* and placing it in the *resources/variables* directory.

**NICEGUI_PORT** – Specifies the port on which the NiceGUI application runs. The default is 8080

**NICEGUI_HOST** – Defines the host address for the NiceGUI server. (0.0.0.0 allows the application to be accessible from any network interface).

### 3.1 Navigation menu

**1) Run ADSORFIT UI:** Launch ADSORFIT to access the main user interface, which is organized into two distinct tabs. The first tab allows users to perform essential computational tasks, such as fitting adsorption models to isotherm data and preprocessing datasets. The second tab provides an intuitive interface for reviewing and adjusting critical adsorption model parameters. Users can specify the maximum number of iterations for data fitting and choose whether to automatically infer column content based on their names. Additionally, users can opt to save multiple CSV files, where the best model is selected and releated results are displayed. Below are snapshots illustrating the layout and functionality of main UI:

![Solver UI snapshot](ADSORFIT/commons/assets/solver_UI.png)

![Models UI snapshot](ADSORFIT/commons/assets/models_UI.png)

**2) Setup and Maintenance:** execute optional commands such as *Install project into environment* to run the developer model project installation, *update project* to pull the last updates from github, and *remove logs* to remove all logs saved in *resources/logs*. 

**3) Exit:** close the program immediately 

### 3.2 Resources
This folder stores both the source data and the results. The adsorption data for fitting must be provided as a CSV file named *adsorption_data.csv*. If automatic column name detection is disabled, the file must include the following columns with these exact names and units: *experiment*, *temperature [K]*, *pressure [Pa]*, and *uptake [mol/g]*. A template of the expected CSV format is available at *resources/templates/adsorption_data.csv*. If the option to automatically detect columns is selected, ADSORFIT will identify target columns based on string pattern matching, and anything even partially matching these keywords will identify the corresponding column:

- **best fit:** collects the best fitting results obtained from different models, if the option is selected during data fitting.

- **logs:** the application logs are saved within this folder

- **templates:** stores the template files for reference

### 4. Configurations
Each model can be configured in the **Model Configuration** tab where you can set an initial guess value for the adsorption model parameters,as well as boundaries for the minimun and maximum expected values.

## 5. License
This project is licensed under the terms of the MIT license. See the LICENSE file for details.



