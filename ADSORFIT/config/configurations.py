# Define variables for fitting
#------------------------------------------------------------------------------
# consider uptake and pressure units as Pa for pressure, mol/g for uptake.

LANGMUIR_GUESS = (0.000001, 10) # initial guess for Langmuir model parameters: K, qsat
LANGMUIR_MAX = (10, 50) # max value for Langmuir model parameters: K, qsat 

SIPS_GUESS = (0.000001, 10, 1) # initial guess for Sips model parameters: K, qsat, N
SIPS_MAX = (10, 10, 50) # max value for Sips model parameters: K, qsat, N 

FREUNDLICH_GUESS = (0.000001, 1) # initial guess for Freundlich model parameters: K, N
FREUNDLICH_MAX = (10, 50) # max value for Freundlich model parameters: K, N 

# Define variables for the training
#------------------------------------------------------------------------------
SEED = 42
MAX_ITERATIONS = 10000

# dictionary of fitting parameters per model (do not modify!)
PARAMETERS = {'langmuir' : [LANGMUIR_GUESS, LANGMUIR_MAX],
              'sips' : [SIPS_GUESS, SIPS_MAX],
              'freundlich' : [FREUNDLICH_GUESS, FREUNDLICH_MAX]}