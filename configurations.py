# Define variables for the dataset
#------------------------------------------------------------------------------
initial_K = 20000
initial_qsat = 0.2


# normalization is to be intended for the final units, which are mol/g for the uptakes
# and Pascal for the pressure (dataset filtered at 20 bar maximal pressure)
#------------------------------------------------------------------------------
pressure_ceil = 2000000
uptake_ceil = 20
min_points = 5

# Define variables for the training
#------------------------------------------------------------------------------
seed = 42


