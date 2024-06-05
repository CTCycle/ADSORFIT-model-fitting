# ADSORFIT: Automated Adsorption Model Fitting

## 1. Project Overview
ADSORFIT is designed to streamline the process of adsorption modeling for researchers in the field. By automating the fitting of theoretical adsorption models to empirical isotherm data, this tool helps in accurately extracting crucial adsorption parameters such as adsorption constants and saturation uptakes. The core functionality revolves around minimizing the Least Squares Sum (LSS) discrepancy between observed and model-predicted uptakes, thereby refining the fit and ensuring the model constants reflect true adsorption behavior under given experimental conditions.

## 2. Installation 
The installation process is designed for simplicity, using .bat scripts to automatically create a virtual environment with all necessary dependencies. Please ensure that Anaconda or Miniconda is installed on your system before proceeding.

- The `scripts/create_environment.bat` file offers a convenient one-click solution to set up your virtual environment.
- Once the environment has been created, run `scripts/package_setup.bat` to install the app package locally.
- **IMPORTANT:** run `scripts/package_setup.bat` if you move the project folder somewhere else after installation, or the app won't work! 

## 3. How to use
The project is organized into subfolders, each dedicated to specific tasks. The `ADSORFIT/utils` folder houses crucial components utilized by various scripts. It's critical to avoid modifying these files, as doing so could compromise the overall integrity and functionality of the program.

**Prepare Your Data**: ensure your adsorption isotherm data is in the `ADSORFIT/data/adsorption_data.csv` file, keeping the header intact to avoid processing errors. The CSV should include columns for experiment, temperature, pressure [Pa], and uptake [mol/g]. Here is a brief summary of the dataset columns:

- `experiment:` ID or name of the experiment used to group data based on individual experiments
- `temperature:` This denotes the temperature of the adsorption isotherm, measured in Kelvin
- `pressure [Pa]:` These are the pressure points of the adsorption isotherm, measured in Pascal
- `uptake [mol/g]` This column contains the uptake measurements of the adsorption isotherm, expressed in mol/g

### Configurations
The configurations.py file allows to change the script configuration. 

| Category            | Setting          | Description                                                     |
|-------------------- |------------------|-----------------------------------------------------------------|
| **Model settings**  | LANGMUIR_GUESS   | Initial guess values for Langmuir adsorption model parameters   |
|                     | LANGMUIR_MAX     | Max value of Langmuir adsorption model parameters               |
|                     | SIPS_GUESS       | Initial guess values for Sips adsorption model parameters       |
|                     | SIPS_MAX         | Max value of Sips adsorption model parameters                   |
|                     | FREUNDLICH_GUESS | Initial guess values for Freundlich adsorption model parameters |
|                     | FREUNDLICH_MAX   | Max value of Freundlich adsorption model parameters             |
| **Fitter settings** | SEED             | Global random seed                                              |
|                     | MAX_ITERATIONS   | Max number of fitting iterations                                | 

## License
This project is licensed under the terms of the MIT license. See the LICENSE file for details.



