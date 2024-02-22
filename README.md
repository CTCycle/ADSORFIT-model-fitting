# ADSORFIT model fitting

## Project Overview
This software is specifically tailored for researchers specializing in adsorption studies. Its primary function is to automate the process of modeling by utilizing theoretical adsorption models, which are usually fitted to empirical adsorption isotherm data, enabling the extraction of significant adsorption constants and other parameters (adsorption constants, uptake at saturation, etc.)

The fitting of models is typically achieved by optimizing the Least Squares (LS) difference between the observed uptake and the uptake predicted by the model given the input pressure. As the LS value reaches its minimum, the fit’s quality improves, indicating that the model’s constants accurately represent the adsorption phenomenon for the specific guest-host pair and experimental temperature. Different models are available depending on the type of adsorption isotherm (see the figure below for more information).

### Objectives
...

## How to use
Execute the ADSORFIT.py file to initiate the script. The source data file, `data/adsorption_data.csv`, serves as the reference for the adsorption isotherm data that will be fitted. It’s crucial to maintain the file header as is; any alterations to the template could lead to errors during script execution. The .csv file comprises the following columns:

- `experiment:` This represents the ID or name of the experiment and is utilized to group data based on individual experiments
- `temperature:` This denotes the temperature of the adsorption isotherm, measured in Kelvin
- `pressure [Pa]:` These are the pressure points of the adsorption isotherm, measured in Pascal
- `uptake [mol/g]` This column contains the uptake measurements of the adsorption isotherm, expressed in mol/g


