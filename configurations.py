# Define variables for the dataset
#------------------------------------------------------------------------------
num_samples = 20000
test_size = 0.2
pad_length = 50
pad_value = 20

# normalization is to be intended for the final units, which are mol/g for the uptakes
# and Pascal for the pressure (dataset filtered at 20 bar maximal pressure)
#------------------------------------------------------------------------------
pressure_ceil = 2000000
uptake_ceil = 20
min_points = 5

# Define variables for the training
#------------------------------------------------------------------------------
seed = 42
training_device = 'GPU'
embedding_dims = 800
epochs = 2000
learning_rate = 0.0001
batch_size = 2500

# define other variables for training
#------------------------------------------------------------------------------
use_tensorboard = True
generate_model_graph = True
XLA_acceleration = True
use_mixed_precision = True
