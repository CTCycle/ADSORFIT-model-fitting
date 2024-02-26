# ADSORFIT: Automated Adsorption Model Fitting

## Project Overview
ADSORFIT is designed to streamline the process of adsorption modeling for researchers in the field. By automating the fitting of theoretical adsorption models to empirical isotherm data, this tool helps in accurately extracting crucial adsorption parameters such as adsorption constants and saturation uptakes. The core functionality revolves around minimizing the Least Squares (LS) discrepancy between observed and model-predicted uptakes, thereby refining the fit and ensuring the model constants reflect true adsorption behavior under given experimental conditions.

### Objectives
...

## Getting started

## Installation 
**Prerequisite:** Ensure Python 3.10.12 is installed on your system.
**Dependencies:** Install all necessary Python packages with:

`pip install -r requirements.txt`

## How to use

**Prepare Your Data**: ensure your adsorption isotherm data is in the `data/adsorption_data.csv` file, keeping the header intact to avoid processing errors. The CSV should include columns for experiment, temperature, pressure [Pa], and uptake [mol/g]. Here is a brief summary of the dataset columns:

- `experiment:` This represents the ID or name of the experiment and is utilized to group data based on individual experiments
- `temperature:` This denotes the temperature of the adsorption isotherm, measured in Kelvin
- `pressure [Pa]:` These are the pressure points of the adsorption isotherm, measured in Pascal
- `uptake [mol/g]` This column contains the uptake measurements of the adsorption isotherm, expressed in mol/g

**Initiate the Script**: Run ADSORFIT.py to start the modeling process.

**Components**
The components directory contains essential scripts and modules for the software's operation. Modifying these could affect the script's functionality.

### Configurations
The configurations.py file allows to change the script configuration. The following parameters are available:

[to continue]

## License
This project is licensed under the terms of the MIT license. See the LICENSE file for details.



