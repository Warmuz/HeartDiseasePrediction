# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

"""Quik overwiev of data"""

data = pd.read_csv('/content/Heart_Disease_Prediction.csv')

data.describe().T

"""Extracting inputs and targets"""

inputs = data.iloc[:,1:-1]
targets = data.iloc[:,-1]

targets = targets.map({'Presence':1, 'Absence':0})  #Converting Categorical data into numerical

"""Balance the dataset"""

one_targets = int(sum(targets))
zero_counter = 0
indices_to_remove = []

for i in range (targets.shape[0]):
  if targets[i] == 0:
    zero_counter += 1
    if zero_counter > one_targets:
      indices_to_remove.append(i)


print("Indices before balancing data:", targets.shape[0])
print("Idices to delete:", len(indices_to_remove) )

balanced_inputs = inputs.drop(indices_to_remove, axis=0)
balanced_targets = targets.drop(indices_to_remove, axis=0)

#reset indices
reset_inputs = balanced_inputs.reset_index(drop=True)
reset_targets = balanced_targets.reset_index(drop=True)

print("Inputs after balancing data:", reset_inputs.shape[0])
print("Targets after balancing data:", reset_targets.shape[0])

"""Standarize the dataset"""

from sklearn import preprocessing
scaled_inputs = preprocessing.scale(reset_inputs)

"""Shuffle data"""

shuffle_indices = np.arange(reset_targets.shape[0])
np.random.shuffle(shuffle_indices)

#the data is randomly spread out
shuffled_inputs = scaled_inputs[shuffle_indices]
shuffled_targets = reset_targets[shuffle_indices]

"""Count how many datata have to be divided into: train, validation and test in propotion: 80%-10%-10%"""

samples_count = shuffled_inputs.shape[0]

train_count = int(samples_count * 0.8)
validation_count = int(samples_count *0.1)
test_count = int(samples_count - train_count-validation_count)

print("Train: %3d, Validation:%3d, Test:%3d" %(train_count, validation_count, test_count))

"""Extract data inot train, validation and test"""

train_inputs = shuffled_inputs[:train_count]
train_targets = shuffled_targets[:train_count]

validation_inputs = shuffled_inputs[train_count:samples_count-validation_count]
validation_targets = shuffled_targets[train_count:samples_count-validation_count]

test_inputs = shuffled_inputs[train_count+validation_count:]
test_targets = shuffled_targets[train_count+validation_count:]

#Checking if proportion is somehow correct
print(np.sum(train_targets), train_count, np.sum(train_targets)/train_count)
print(np.sum(validation_targets), validation_count, np.sum(validation_targets)/validation_count)
print(np.sum(test_targets), test_count, np.sum(test_targets)/test_count)

"""Save to npz format"""

np.savez('Heart_Diesase_Prediction_train', inputs=train_inputs, targets=train_targets)
np.savez('Heart_Diesase_Prediction_validation', inputs=validation_inputs, targets=validation_targets)
np.savez('Heart_Diesase_Prediction_test', inputs=test_inputs, targets=test_targets)

"""Creating an iterator for Batching"""

class Heart_Disease_Data():
    # Dataset is a mandatory arugment, while the batch_size is optional
    # If you don't input batch_size, it will automatically take the value: None
    def __init__(self, dataset, batch_size = None):
    
        # The dataset that loads is one of "train", "validation", "test".
        # e.g. if I call this class with x('train',5), it will load 'Audiobooks_data_train.npz' with a batch size of 5.
        npz = np.load('Heart_Diesase_Prediction_{0}.npz'.format(dataset))
        
        # Two variables that take the values of the inputs and the targets. Inputs are floats, targets are integers
        self.inputs, self.targets = npz['inputs'].astype(np.float), npz['targets'].astype(np.int)
        
        # Counts the batch number, given the size you feed it later
        # If the batch size is None, we are either validating or testing, so we want to take the data in a single batch
        if batch_size is None:
            self.batch_size = self.inputs.shape[0]
        else:
            self.batch_size = batch_size
        self.curr_batch = 0
        self.batch_count = self.inputs.shape[0] // self.batch_size
    
    # A method which loads the next batch
    def __next__(self):
        if self.curr_batch >= self.batch_count:
            self.curr_batch = 0
            raise StopIteration()
            
        # You slice the dataset in batches and then the "next" function loads them one after the other
        batch_slice = slice(self.curr_batch * self.batch_size, (self.curr_batch + 1) * self.batch_size)
        inputs_batch = self.inputs[batch_slice]
        targets_batch = self.targets[batch_slice]
        self.curr_batch += 1
        
        # One-hot encode the targets. In this example it's a bit superfluous since we have a 0/1 column 
        # as a target already but we're giving you the code regardless, as it will be useful for any 
        # classification task with more than one target column
        classes_num = 2
        targets_one_hot = np.zeros((targets_batch.shape[0], classes_num))
        targets_one_hot[range(targets_batch.shape[0]), targets_batch] = 1
        
        # The function will return the inputs batch and the one-hot encoded targets
        return inputs_batch, targets_one_hot
    
        
    # A method needed for iterating over the batches, as we will put them in a loop
    # This tells Python that the class we're defining is iterable, i.e. that we can use it like:
    # for input, output in data: 
        # do things
    # An iterator in Python is a class with a method __next__ that defines exactly how to iterate through its objects
    def __iter__(self):
        return self

import tensorflow as tf

input_size = 12
output_size = 2
hidden_layer = 50

from tensorflow.python.framework import ops
ops.reset_default_graph()

import tensorflow.compat.v1 as tf
tf.disable_v2_behavior() 

inputs = tf.placeholder(tf.float32,[None, input_size])
targets = tf.placeholder(tf.int64,[None, output_size])

# Outline the model. We will create a net with 2 hidden layers
weights_1 = tf.get_variable("weights_1", [input_size, hidden_layer])
biases_1 = tf.get_variable("biases_1", [hidden_layer])
outputs_1 = tf.nn.relu(tf.matmul(inputs, weights_1) + biases_1)

weights_2 = tf.get_variable("weights_2", [hidden_layer, hidden_layer])
biases_2 = tf.get_variable("biases_2", [hidden_layer])
outputs_2 = tf.nn.sigmoid(tf.matmul(outputs_1, weights_2) + biases_2)

weights_3 = tf.get_variable("weights_3", [hidden_layer, output_size])
biases_3 = tf.get_variable("biases_3", [output_size])
# We will incorporate the softmax activation into the loss, as in the previous example
outputs = tf.matmul(outputs_2, weights_3) + biases_3

loss = tf.nn.softmax_cross_entropy_with_logits_v2(logits = outputs, labels=targets)
mean_loss = tf.reduce_mean(loss)

# Get a 0 or 1 for every input indicating whether it output the correct answer
out_equals_target = tf.equal(tf.argmax(outputs, 1), tf.argmax(targets, 1))
accuracy = tf.reduce_mean(tf.cast(out_equals_target, tf.float32))

# Optimize with Adam
optimize = tf.train.AdamOptimizer(learning_rate=0.0001).minimize(mean_loss)

"""Initialization"""

sess = tf.InteractiveSession()
initializer=tf.global_variables_initializer()
sess.run(initializer)

batch_size = 50
max_epochs = 100
prev_validation_loss = 9999999.

train_data = Heart_Disease_Data('train', batch_size)
validation_data = Heart_Disease_Data('validation')

"""Training and validation data"""

validation_list = []
for epoch_counter in range(max_epochs):
    
    # Set the epoch loss to 0, and make it a float
    curr_epoch_loss = 0.
    
    # Iterate over the training data 
    # Since train_data is an instance of the Audiobooks_Data_Reader class,
    # we can iterate through it by implicitly using the __next__ method we defined above.
    # As a reminder, it batches samples together, one-hot encodes the targets, and returns
    # inputs and targets batch by batch
    for input_batch, target_batch in train_data:
        _, batch_loss = sess.run([optimize, mean_loss], 
            feed_dict={inputs: input_batch, targets: target_batch})
        
        #Record the batch loss into the current epoch loss
        curr_epoch_loss += batch_loss
    
    # Find the mean curr_epoch_loss
    # batch_count is a variable, defined in the Audiobooks_Data_Reader class
    curr_epoch_loss /= train_data.batch_count
    
    # Set validation loss and accuracy for the epoch to zero
    validation_loss = 0.
    validation_accuracy = 0.
    
    # Use the same logic of the code to forward propagate the validation set
    # There will be a single batch, as the class was created in this way
    for input_batch, target_batch in validation_data:
        validation_loss, validation_accuracy = sess.run([mean_loss, accuracy],
            feed_dict={inputs: input_batch, targets: target_batch})
    
    
    # Print statistics for the current epoch
    print('Epoch '+str(epoch_counter+1)+
          '. Training loss: '+'{0:.3f}'.format(curr_epoch_loss)+
          '. Validation loss: '+'{0:.3f}'.format(validation_loss)+
          '. Validation accuracy: '+'{0:.2f}'.format(validation_accuracy * 100.)+'%')
    validation_list.append(validation_accuracy*100)
    
    # Trigger early stopping if validation loss begins increasing.
    if validation_loss > prev_validation_loss:
        break
        
    # Store this epoch's validation loss to be used as previous in the next iteration.
    prev_validation_loss = validation_loss

plt.plot(validation_list)
plt.title("Validation loss")
plt.xlabel('epochs')
plt.ylabel('accuracy [%]')
plt.show()
