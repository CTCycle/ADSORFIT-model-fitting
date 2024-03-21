# ADSORFIT: Automated Adsorption Model Fitting

## 1. Project Overview
ADSORFIT is designed to streamline the process of adsorption modeling for researchers in the field. By automating the fitting of theoretical adsorption models to empirical isotherm data, this tool helps in accurately extracting crucial adsorption parameters such as adsorption constants and saturation uptakes. The core functionality revolves around minimizing the Least Squares Sum (LSS) discrepancy between observed and model-predicted uptakes, thereby refining the fit and ensuring the model constants reflect true adsorption behavior under given experimental conditions.

## 2. Installation
First, ensure that you have Python 3.10.12 installed on your system. Then, you can easily install the required Python packages using the provided requirements.txt file:

`pip install -r requirements.txt` 

## 3. How to use
Run ADSORFIT.py to start the modeling process. The `utils/` folder houses crucial components utilized by various scripts. It's critical to avoid modifying these files, as doing so could compromise the overall integrity and functionality of the program. 

**Prepare Your Data**: ensure your adsorption isotherm data is in the `data/adsorption_data.csv` file, keeping the header intact to avoid processing errors. The CSV should include columns for experiment, temperature, pressure [Pa], and uptake [mol/g]. Here is a brief summary of the dataset columns:

- `experiment:` ID or name of the experiment used to group data based on individual experiments
- `temperature:` This denotes the temperature of the adsorption isotherm, measured in Kelvin
- `pressure [Pa]:` These are the pressure points of the adsorption isotherm, measured in Pascal
- `uptake [mol/g]` This column contains the uptake measurements of the adsorption isotherm, expressed in mol/g


### Configurations
The configurations.py file allows to change the script configuration. The following parameters are available:

| Category           | Setting          | Description                                               |
|--------------------|------------------|-----------------------------------------------------------|
| **Model settings** | langmuir_guess   | Initial guess values for Langmuir adsorption model parameters |
|                    | langmuir_max     | Max value of Langmuir adsorption model parameters         |
|                    | sips_guess       | Initial guess values for Sips adsorption model parameters |
|                    | sips_max         | Max value of Sips adsorption model parameters             |
|                    | freundlich_guess | Initial guess values for Freundlich adsorption model parameters |
|                    | freundlich_max   | Max value of Freundlich adsorption model parameters       |
| **Fitter settings** | seed            | Global random seed                                        |
|                    | max_iterations   | Max number of fitting iterations                          |
 

## License
This project is licensed under the terms of the MIT license. See the LICENSE file for details.



