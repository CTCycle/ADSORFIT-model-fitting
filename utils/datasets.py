import os
from tqdm import tqdm
tqdm.pandas()

           
# [DATASET OPERATIONS]
#==============================================================================
#==============================================================================
class AdaptDataSet:

    def __init__(self, fitting_data):
        self.results = fitting_data        

    #--------------------------------------------------------------------------
    def expand_fitting_data(self, dataset):

        langmuir_data = [d['langmuir'] for d in self.results]
        sips_data = [d['sips'] for d in self.results]
        freundlich_data = [d['freundlich'] for d in self.results]

        # Langmuir adsorption model
        dataset['langmuir K'] = [x['optimal_params'][0] for x in langmuir_data]
        dataset['langmuir qsat'] = [x['optimal_params'][1] for x in langmuir_data]
        dataset['langmuir K error'] =[x['errors'][0] for x in langmuir_data]
        dataset['langmuir qsat error'] = [x['errors'][1] for x in langmuir_data]
        dataset['langmuir LSS'] = [x['LSS'] for x in langmuir_data]

        # Sips adsorption model
        dataset['sips K'] = [x['optimal_params'][0] for x in sips_data]
        dataset['sips qsat'] = [x['optimal_params'][1] for x in sips_data]
        dataset['sips N'] = [x['optimal_params'][2] for x in sips_data]
        dataset['sips K error'] =[x['errors'][0] for x in sips_data]
        dataset['sips qsat error'] = [x['errors'][1] for x in sips_data]
        dataset['sips N error'] = [x['errors'][2] for x in sips_data]
        dataset['sips LSS'] = [x['LSS'] for x in sips_data]

        # Freundlich adsorption model
        dataset['freundlich K'] = [x['optimal_params'][0] for x in freundlich_data]        
        dataset['freundlich N'] = [x['optimal_params'][1] for x in freundlich_data]
        dataset['freundlich K error'] =[x['errors'][0] for x in freundlich_data]        
        dataset['freundlich N error'] = [x['errors'][1] for x in freundlich_data]   
        dataset['freundlich LSS'] = [x['LSS'] for x in freundlich_data]     

        return dataset
    
    #--------------------------------------------------------------------------
    def find_best_model(self, dataset):
        LSS_columns = [x for x in dataset.columns if 'LSS' in x]
        dataset['best model'] = dataset[LSS_columns].apply(lambda x : x.idxmin(), axis=1)
        dataset['best model'] = dataset['best model'].apply(lambda x : x.replace(' LSS', ''))
        dataset['worst model'] = dataset[LSS_columns].apply(lambda x : x.idxmax(), axis=1)
        dataset['worst model'] = dataset['worst model'].apply(lambda x : x.replace(' LSS', ''))

        return dataset
    
    #--------------------------------------------------------------------------
    def save_best_fitting(self, models, dataset, path):
        for mod in models:
            df = dataset[dataset['best model'] == mod]
            model_cols = [x for x in df.columns if mod in x]
            target_cols = [x for x in df.columns[:8]] + model_cols
            df_model = df[target_cols]
            file_loc = os.path.join(path, f'{mod}_best_fit.csv') 
            df_model.to_csv(file_loc, index=False, sep=';', encoding='utf-8')
                    


   
        
    