import os
import sqlite3
import pandas as pd

from ADSORFIT.commons.constants import DATA_PATH
from ADSORFIT.commons.logger import logger

# [DATABASE]
###############################################################################
class ADSORFITDatabase:

    def __init__(self):             
        self.db_path = os.path.join(DATA_PATH, 'ADSORFIT_database.db')  

    #--------------------------------------------------------------------------
    def save_adsorption_data(self, data : pd.DataFrame): 
        # connect to sqlite database and save the preprocessed data as table
        conn = sqlite3.connect(self.db_path)         
        data.to_sql('ADSORPTION_DATA', conn, if_exists='replace')
        conn.commit()
        conn.close()                

    #--------------------------------------------------------------------------
    def save_fitting_results(self, data : pd.DataFrame): 
        # connect to sqlite database and save the preprocessed data as table
        conn = sqlite3.connect(self.db_path)         
        data.to_sql('ADSORPTION_FITTING_RESULTS', conn, if_exists='replace')
        conn.commit()
        conn.close() 

    #--------------------------------------------------------------------------
    def save_best_fit(self, data : pd.DataFrame, table_name='BEST_FIT'): 
        # connect to sqlite database and save the preprocessed data as table
        conn = sqlite3.connect(self.db_path)         
        data.to_sql(table_name, conn, if_exists='replace')
        conn.commit()
        conn.close() 
        

    