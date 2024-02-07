import sys

# set warnings
#------------------------------------------------------------------------------
import warnings
warnings.simplefilter(action='ignore', category = Warning)

# import modules and classes
#------------------------------------------------------------------------------
from modules.components.data_classes import UserOperations

# [MAIN MENU]
#==============================================================================
# module for the selection of different operations
#==============================================================================
user_operations = UserOperations()
operations_menu = {'1' : '.....',                   
                   '2' : '.....',                                    
                   '3' : '.....'}

while True:    
    op_sel = user_operations.menu_selection(operations_menu)
    print()      
    if op_sel == 1:
        import modules.SCADS_preprocessing
        del sys.modules['modules.SCADS_preprocessing']
 
    elif op_sel == 2:
        pass 

    elif op_sel == 3:
        break      
    
 
