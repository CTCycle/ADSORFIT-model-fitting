# Define variables for fitting
#------------------------------------------------------------------------------
# consider uptake and pressure units as Pa for pressure, mol/g for uptake.

Langmuir_guess = (0.000001, 10) # initial guess for Langmuir model parameters: K, qsat
Langmuir_max = (1.0, 10) # max value for Langmuir model parameters: K, qsat 

Sips_guess = (0.000001, 10, 1) # initial guess for Sips model parameters: K, qsat, N
Sips_max = (1.0, 10, 50) # max value for Sips model parameters: K, qsat, N 

# dictionary of fitting parameters per model
parameters = {'Langmuir' : [Langmuir_guess, Langmuir_max],
              'Sips' : [Sips_guess, Sips_max]}

# Define variables for the training
#------------------------------------------------------------------------------
seed = 42
max_iterations = 60000


