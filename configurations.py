# Define variables for fitting
#------------------------------------------------------------------------------
# consider uptake and pressure units as Pa for pressure, mol/g for uptake.

langmuir_guess = (0.000001, 10) # initial guess for Langmuir model parameters: K, qsat
langmuir_max = (1.0, 10) # max value for Langmuir model parameters: K, qsat 

sips_guess = (0.000001, 10, 1) # initial guess for Sips model parameters: K, qsat, N
sips_max = (1.0, 10, 50) # max value for Sips model parameters: K, qsat, N 

# dictionary of fitting parameters per model
parameters = {'langmuir' : [langmuir_guess, langmuir_max],
              'sips' : [sips_guess, sips_max]}

# Define variables for the training
#------------------------------------------------------------------------------
seed = 42
max_iterations = 1000


