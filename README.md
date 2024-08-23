# ADSORFIT: Automated Adsorption Model Fitting

## 1. Project Overview
ADSORFIT is designed to streamline the process of adsorption modeling for researchers in the field. By automating the fitting of theoretical adsorption models to empirical isotherm data, this tool helps in accurately extracting crucial adsorption parameters such as adsorption constants and saturation uptakes. The core functionality revolves around minimizing the Least Squares Sum (LSS) discrepancy between observed and model-predicted uptakes, thereby refining the fit and ensuring the model constants reflect true adsorption behavior under given experimental conditions.

## 2. Installation 
The installation process is designed for simplicity, using .bat scripts to automatically create a virtual environment with all necessary dependencies. Please ensure that Anaconda or Miniconda is installed on your system before proceeding.

- The `scripts/create_environment.bat` file offers a convenient one-click solution to set up your virtual environment.
- Once the environment has been created, run `scripts/package_setup.bat` to install the app package locally.
- **IMPORTANT:** run `scripts/package_setup.bat` if you move the project folder somewhere else after installation, or the app won't work! 

## 3. How to use

### Prepare Your Data
Ensure your adsorption isotherm data is in the `resources/adsorption_data.csv` file, keeping the header intact to avoid processing errors. The CSV should include columns for experiment, temperature, pressure [Pa], and uptake [mol/g]. Here is a brief summary of the dataset columns:

- `experiment:` ID or name of the experiment used to group data based on individual experiments
- `temperature:` This denotes the temperature of the adsorption isotherm, measured in Kelvin
- `pressure [Pa]:` These are the pressure points of the adsorption isotherm, measured in Pascal
- `uptake [mol/g]` This column contains the uptake measurements of the adsorption isotherm, expressed in mol/g

### Configurations
For customization, you can modify the main script parameters via the `ADSORFIT/commons/configurations.py` file. 

#### Model settings  
Each model can be configured using the following settings, where you can set a value for all model parameters.

| Setting          | Description                                                     |
|------------------|-----------------------------------------------------------------|
| MODEL_INITIAL    | Initial guess values for Langmuir adsorption model parameters   |
| MODEL_MIN        | Minimun value of Langmuir adsorption model parameters           |
| MODEL_MAX        | Initial guess values for Sips adsorption model parameters       |

#### Fit settings

| SEED             | Global random seed                                              |
| MAX_ITERATIONS   | Max number of fitting iterations                                |
| SELECTED_MODELS  | Currently selected model for fitting                            |

## License
This project is licensed under the terms of the MIT license. See the LICENSE file for details.



