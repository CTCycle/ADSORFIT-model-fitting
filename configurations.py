# Define variables for fitting
#------------------------------------------------------------------------------
# consider uptake and pressure units as Pa for pressure, mol/g for uptake.

langmuir_guess = (0.000001, 10) # initial guess for Langmuir model parameters: K, qsat
langmuir_max = (10, 50) # max value for Langmuir model parameters: K, qsat 

sips_guess = (0.000001, 10, 1) # initial guess for Sips model parameters: K, qsat, N
sips_max = (10, 10, 50) # max value for Sips model parameters: K, qsat, N 

freundlich_guess = (0.000001, 1) # initial guess for Freundlich model parameters: K, N
freundlich_max = (10, 50) # max value for Freundlich model parameters: K, N 

# Define variables for the training
#------------------------------------------------------------------------------
seed = 42
max_iterations = 10000

# dictionary of fitting parameters per model (do not modify!)
parameters = {'langmuir' : [langmuir_guess, langmuir_max],
              'sips' : [sips_guess, sips_max],
              'freundlich' : [freundlich_guess, freundlich_max]}