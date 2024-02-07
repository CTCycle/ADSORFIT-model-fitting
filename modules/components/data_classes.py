import os
import math
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import curve_fit
from tensorflow.keras.preprocessing.sequence import pad_sequences 
from tqdm import tqdm
tqdm.pandas()

# ...
#==============================================================================
#==============================================================================
#==============================================================================
class UserOperations:
    
    """    
    A class for user operations such as interactions with the console, directories and files
    cleaning and other maintenance operations.
      
    Methods:
        
    menu_selection(menu):  console menu management 
    clear_all_files(path): remove files and directories
   
    """
    
    # print custom menu on console and allows selecting an option
    #--------------------------------------------------------------------------
    def menu_selection(self, menu):        
        
        """        
        menu_selection(menu)
        
        Presents a custom menu to the user and returns the selected option.
        
        Keyword arguments:                      
            menu (dict): A dictionary containing the options to be presented to the user. 
                         The keys are integers representing the option numbers, and the 
                         values are strings representing the option descriptions.
        
        Returns:            
            op_sel (int): The selected option number.
        
        """        
        indexes = [idx + 1 for idx, val in enumerate(menu)]
        for key, value in menu.items():
            print('{0} - {1}'.format(key, value))            
        
        print()
        while True:
            try:
                op_sel = int(input('Select the desired operation: '))
            except:
                continue            
            
            while op_sel not in indexes:
                try:
                    op_sel = int(input('Input is not valid, please select a valid option: '))
                except:
                    continue
            break
        
        return op_sel        
    

# ...
#==============================================================================
#==============================================================================
#==============================================================================
class AdsorptionModels:

    def __init__(self):        
        self.lower_bounds = [0, 0]  
        self.upper_bounds = [1, 10000] 
        self.bounds = (self.lower_bounds, self.upper_bounds)    
    
    #==========================================================================
    def Langmuir_model(self, P, k, qsat):        
        kP = P * k
        qe = qsat * (kP/(1 + kP))
        
        return qe
    
   
    #==========================================================================
    def Sips_model(self, P, k, N, qsat):        
        kP = (P * k)**N
        qe = qsat * (kP/(1 + kP)**N)
        
        return qe
    

    #==========================================================================
    def adsmodel_fitter(self, col_x, col_y, model, separator):        

        array_x = np.array([float(x) for x in col_x.split(separator)])
        array_y = np.array([float(y) for y in col_y.split(separator)])
        max_Y = array_y.max()       

        self.models = {'Langmuir' : [self.Langmuir_model, [0.000001, 10], ([0, 0], [10, 1000])]}
        parameters = {}        
        for name, vals in self.models.items():
            model = vals[0]
            p0_values = vals[1]
            bounds = vals[2]
            try:
                popt, pcov = curve_fit(model, array_x, array_y, sigma=None, check_finite=True,
                                   p0 = p0_values, bounds=bounds, full_output=False, maxfev=200000)                
                self.param_per_model = {name : popt}
                parameters.update(self.param_per_model)   
            except:
                self.param_per_model = {name : ('NA', 'NA')}
                parameters.update(self.param_per_model)

        k_Langmuir, qsat_Langmuir = parameters['Langmuir']              

        return k_Langmuir, qsat_Langmuir             


# [DATA PREPROCESSING]
#==============================================================================
# preprocess adsorption data
#==============================================================================
class PreProcessing:
    
    """ 
    A class for preprocessing operations in pointwise fashion (with expanded dataset).
    Includes many different methods that can be used in sequence to build a functional
    preprocessing pipeline.
      
    Methods:
        
    __init__(df_SC, df_BN): initializes the class with the single component 
                            and binary mixrture datasets
    
    dataset_splitting():    splits dataset into train, test and validation sets

    """  

    #--------------------------------------------------------------------------
    def pressure_converter(self, type, original_P):

        '''
        pressure_converter(type, original_P)

        Converts pressure from the specified unit to Pascals.

        Keyword arguments:
            type (str): The original unit of pressure.
            original_P (int or float): The original pressure value.

        Returns:
            P_value (int): The pressure value converted to Pascals.

        '''           
        P_unit = type
        if P_unit == 'bar':
            P_value = int(original_P * 100000)        
                
        return P_value 

    #--------------------------------------------------------------------------
    def uptake_converter(self, q_unit, q_val, mol_weight):

        '''
        uptake_converter(q_unit, q_val, mol_weight)

        Converts the uptake value from the specified unit to moles per gram.

        Keyword arguments:
            q_unit (str):              The original unit of uptake.
            q_val (int or float):      The original uptake value.
            mol_weight (int or float): The molecular weight of the adsorbate.

        Returns:
            Q_value (float): The uptake value converted to moles per gram

        '''
        Q_value = q_val
        if q_unit in ('mmol/g', 'mol/kg'):
            Q_value = q_val/1000 
        elif q_unit == 'mol/g':
            Q_value = q_val
        elif q_unit == 'mmol/kg':
            Q_value = q_val/1000000
        elif q_unit == 'mg/g':
            Q_value = q_val/1000/float(mol_weight)            
        elif q_unit == 'g/g':
            Q_value = (q_val/float(mol_weight))                                   
        elif q_unit == 'wt%':                
            Q_value = ((q_val/100)/float(mol_weight))          
        elif q_unit in ('g Adsorbate / 100g Adsorbent', 'g/100g'):              
            Q_value = ((q_val/100)/float(mol_weight))                            
        elif q_unit in ('ml(STP)/g', 'cm3(STP)/g'):
            Q_value = q_val/22.414      
                
        return Q_value        
        
    #--------------------------------------------------------------------------
    def properties_assigner(self, df_isotherms, df_adsorbates):

        df_properties = df_adsorbates[['name', 'complexity', 'atoms', 'mol_weight', 'covalent_units', 'H_acceptors', 'H_donors', 'heavy_atoms']]
        df_properties = df_properties.rename(columns = {'name': 'adsorbates_name'})
        df_isotherms['adsorbates_name'] = df_isotherms['adsorbates_name'].apply(lambda x : x.lower())
        df_properties['adsorbates_name'] = df_properties['adsorbates_name'].apply(lambda x : x.lower())
        df_adsorption = pd.merge(df_isotherms, df_properties, on = 'adsorbates_name', how='left')
        df_adsorption = df_adsorption.dropna().reset_index(drop=True)

        return df_adsorption    
    
    # preprocessing model for tabular data using Keras pipeline    
    #--------------------------------------------------------------------------  
    def series_preprocessing(self, series, str_output=False, padding=True, normalization=True,
                             upper=None, pad_value=20, pad_length=10):

        '''
        Normalizes a series of values.
    
        Keyword arguments:
            series (list): A list of values to be normalized
    
        Returns:
            list: A list of normalized values
        
        '''
        processed_series = series 
        if normalization == True:  
            if upper != None:
                processed_series = [x/upper for x in series]
            else:
                max_val = max([float(g) for g in series])
                if max_val == 0.0:
                    max_val = 10e-14
                processed_series = [x/max_val for x in series]
        if padding == True:
            processed_series = pad_sequences([processed_series], maxlen = pad_length, 
                                              value = pad_value, dtype = 'float32', padding = 'post')
            pp_seq = processed_series[0]

        if str_output == True:
            pp_seq = ' '.join([str(x) for x in pp_seq])

        return pp_seq        
        
    #--------------------------------------------------------------------------
    def model_savefolder(self, path, model_name):

        '''
        Creates a folder with the current date and time to save the model.
    
        Keyword arguments:
            path (str):       A string containing the path where the folder will be created.
            model_name (str): A string containing the name of the model.
    
        Returns:
            str: A string containing the path of the folder where the model will be saved.
        
        '''        
        raw_today_datetime = str(datetime.now())
        truncated_datetime = raw_today_datetime[:-10]
        today_datetime = truncated_datetime.replace(':', '').replace('-', '').replace(' ', 'H') 
        model_name = f'{model_name}_{today_datetime}'
        model_savepath = os.path.join(path, model_name)
        if not os.path.exists(model_savepath):
            os.mkdir(model_savepath)               
            
        return model_savepath      

# define class for correlations calculations
#==============================================================================
#==============================================================================
#==============================================================================
class MultiCorrelator:
    
    ''' 
    MultiCorrelator(dataframe)
    
    Calculates the correlation matrix of a given dataframe using specific methods.
    The internal functions retrieves correlations based on Pearson, Spearman and Kendall
    methods. This class is also used to plot the correlation heatmap and filter correlations
    from the original matrix based on given thresholds. Returns the correlation matrix
    
    Keyword arguments: 
        
    dataframe (pd.dataframe): target dataframe
    
    Returns:
        
    df_corr (pd.dataframe): correlation matrix in dataframe form
                
    '''
    def __init__(self, dataframe):
        self.dataframe = dataframe
        
    # Spearman correlation calculation
    #==========================================================================
    def Spearman_corr(self, decimals):
        self.df_corr = self.dataframe.corr(method = 'spearman').round(decimals)
        return self.df_corr
    
    # Kendall correlation calculation
    #==========================================================================    
    def Kendall_corr(self, decimals):
        self.df_corr = self.dataframe.corr(method = 'kendall').round(decimals)
        return self.df_corr
    
    # Pearson correlation calculation
    #==========================================================================   
    def Pearson_corr(self, decimals):
        self.df_corr = self.dataframe.corr(method = 'pearson').round(decimals)
        return self.df_corr
    
    # plotting correlation heatmap using seaborn package
    #==========================================================================
    def corr_heatmap(self, matrix, path, dpi, name):
        
        ''' 
        corr_heatmap(matrix, path, dpi, name)
        
        Plot the correlation heatmap using the seaborn package. The plot is saved 
        in .jpeg format in the folder that is specified through the path argument. 
        Output quality can be tuned with the dpi argument.
        
        Keyword arguments:    
            
        matrix (pd.dataframe): target correlation matrix
        path (str):            picture save path for the .jpeg file
        dpi (int):             value to set picture quality when saved (int)
        name (str):            name to be added in title and filename
        
        Returns:
            
        None
            
        '''                
        cmap = 'viridis'
        fig, ax = plt.subplots(figsize=(10, 10))
        sns.heatmap(matrix, square = True, annot = False, 
                    mask = False, cmap = cmap, yticklabels = True, 
                    xticklabels = True)
        plt.title('{}_correlation_heatmap'.format(name))
        plt.xticks(rotation=75, fontsize=8) 
        plt.yticks(rotation=45, fontsize=8) 
        plt.tight_layout()
        plot_loc = os.path.join(path, '{}_correlation_heatmap.jpeg'.format(name))
        plt.savefig(plot_loc, bbox_inches='tight', format ='jpeg', dpi = dpi)
        plt.show(block = False)
        plt.close()    
     
    # filtering of correlation pairs based on threshold value. Strong, weak and null
    # pairs are isolated and embedded into output lists
    #==========================================================================   
    def corr_filter(self, matrix, threshold): 
        
        '''
        corr_filter(matrix, path, dpi)
        
        Generates filtered lists of correlation pairs, based on the given threshold.
        Weak correlations are those below the threshold, strong correlations are those
        above the value and zero correlations identifies all those correlation
        with coefficient equal to zero. Returns the strong, weak and zero pairs lists
        respectively.
        
        Keyword arguments:    
        matrix (pd.dataframe): target correlation matrix
        threshold (float):     threshold value to filter correlations coefficients
        
        Returns:
            
        strong_pairs (list): filtered strong pairs
        weak_pairs (list):   filtered weak pairs
        zero_pairs (list):   filtered zero pairs
                       
        '''        
        self.corr_pairs = matrix.unstack()
        self.sorted_pairs = self.corr_pairs.sort_values(kind="quicksort")
        self.strong_pairs = self.sorted_pairs[(self.sorted_pairs) >= threshold]
        self.strong_pairs = self.strong_pairs.reset_index(level = [0,1])
        mask = (self.strong_pairs.level_0 != self.strong_pairs.level_1) 
        self.strong_pairs = self.strong_pairs[mask]
        
        self.weak_pairs = self.sorted_pairs[(self.sorted_pairs) >= -threshold]
        self.weak_pairs = self.weak_pairs.reset_index(level = [0,1])
        mask = (self.weak_pairs.level_0 != self.weak_pairs.level_1) 
        self.weak_pairs = self.weak_pairs[mask]
        
        self.zero_pairs = self.sorted_pairs[(self.sorted_pairs) == 0]
        self.zero_pairs = self.zero_pairs.reset_index(level = [0,1])
        mask = (self.zero_pairs.level_0 != self.zero_pairs.level_1) 
        self.zero_pairs_P = self.zero_pairs[mask]
        
        return self.strong_pairs, self.weak_pairs, self.zero_pairs
    




  