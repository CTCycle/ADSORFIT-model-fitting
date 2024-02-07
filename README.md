# ADSCON model fitting

## Project Overview
This project delves into the fascinating world of adsorption, a surface-based process where a film of particles (adsorbate) accumulate on the surface of a material (adsorbent). This phenomenon plays a pivotal role in numerous industries. For instance, it’s instrumental in water treatment facilities for the purification of water, in air filters to improve air quality, and in the automotive industry within catalytic converters to reduce harmful emissions. The adsorption of compounds is usually quantified by measuring the adsorption isotherm a given adsorbate/adsorbent combination, meaning that 

### Objectives
The objective of this project is to harness the power of machine learning to predict the adsorption of chemicals on adsorbent materials. The aim is to build a model that can accurately predict the adsorbed amount of a specific guest-host combination under various conditions, by leveraging the data from the NIST/ARPA-E Database. This could have significant implications for industries that rely on these materials, potentially leading to more efficient processes and better materials design. As such, this project takes a different approach compared to fitting adsorption data with theoretical model for adsorption constants calculation, instead proposing the use of a deep learning approach to understand adsorption isotherm patterns by leveraging a large volume of experimental data.

### Data source
The NIST/ARPA-E Database of Novel and Emerging Adsorbent Materials is a free, web-based catalog of adsorbent materials and measured adsorption properties of numerous materials obtained from article entries from the scientific literature. Search fields for the database include adsorbent material, adsorbate gas, experimental conditions (pressure, temperature), and bibliographic information (author, title, journal), and results from queries are provided as a list of articles matching the search parameters. The database also contains adsorption isotherms digitized from the cataloged articles, which can be compared visually online in the web application or exported for offline analytics.

The data used for the machine learning training has been extracted using another python application I wrote togehter with this one (see https://github.com/CTCycle/NISTADS-data-collection), which makes use of the NIST/ARPA-E Database API to collect adsorption isotherm data for both single component experiments and binary mixture experiments. Such script can also perform chemical data mining to add chemical features for the sorbates included in the adsorption isotherm dataset. The two generate datasets (single component and binary mixture data) must be used as input data for the deep learning model training and evaluation.

## How to use
The Python-based application for this project is organized into several submodules, each performing distinct operations. This includes data preprocessing and model training/evaluation. Run the NISTADS_main.py file to launch the script and use the main menu to navigate the different options.

**The main options are as following:**
1) SCADS framework: training and predictions                   
2) BNADS framework: training and predictions                                    
3) Exit and close

**Any of the first two options** will open a submenu to select operations for the selected DNN model:
1) Preprocess data for MODELNAME model training
2) Pretrain MODELNAME model
3) Validation of pretrained models
4) Predict adsorption of compounds            
5) Go back to main menu

### Data preprocessing
This module handles the cleaning and preprocessing of the previosuly extracted data, including conversion of pressure and uptake to a common unit: Pascal (Pa) is used for pressure, while mol/g is used for the adsorbed amount. It includes functions for handling missing values, outliers, and data normalization. 

### Model training
This module contains the machine learning algorithms used to train the model. It includes functions for model selection, hyperparameter tuning, and cross-validation to ensure the robustness of the model.

### Model evaluation
This module is used to evaluate the performance of the trained model using various metrics such as Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and R-squared (R²) score.

### Adsorption prediction
Predict adsorption of compounds from input properties (guest and guest parameters, host, temperature) and given pressure series (in Pascal).The results are saved in a .csv file in the results folder.

### Requirements
This application has been developed and tested using the following dependencies (Python 3.10.12):

- `keras==2.10.0`
- `matplotlib==3.7.2`
- `numpy==1.25.2`
- `pandas==2.0.3`
- `scikit-learn==1.3.0`
- `scipy==1.11.2`
- `seaborn==0.12.2`
- `tensorflow==2.10.0`
- `tqdm==4.66.1`
- `xlrd==2.0.1`
- `XlsxWriter==3.1.3`

These dependencies are specified in the provided `requirements.txt` file to ensure full compatibility with the application. 

## Future Work
The project is ongoing, and future work will focus on improving the accuracy of the model by incorporating more sophisticated machine learning algorithms and exploring more feature engineering techniques. Additionally, efforts will be made to update the model as new data becomes available in the NIST/ARPA-E Database.
