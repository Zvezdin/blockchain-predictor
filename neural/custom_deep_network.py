from neural_network import NeuralNetwork

import numpy as np
import tensorflow as tf

class CustomDeepNetwork(NeuralNetwork):
	def __init__(self):
		self.name="CustomDeep"

	def train(self, givenDataset, givenLabels):
		dataset = {}
		labels = {}

		image_width = 100
		image_height = 7
		num_labels = 2


		for kind in ['train', 'valid', 'test']:
			print("Reformatting dataset with shape", givenDataset[kind].shape)
			dataset[kind], labels[kind] = self.reformat(givenDataset[kind], givenLabels[kind], image_width, image_height, num_labels)
			print(kind, 'set', dataset[kind].shape, labels[kind].shape)

		print(labels)

		run_train(dataset, labels, image_width, image_height, num_labels)

	def predict(self, dataset):
		""

def build_network(dataset, batch_size, image_width, image_height, num_labels, hidden_layers, hidden_nodes, dropoutIndex, activation):
	def weight_variable(shape):
		initial = tf.truncated_normal(shape, stddev=0.05)
		return tf.Variable(initial)
		#return tf.Variable(tf.zeros(shape))

	def bias_variable(shape):
		initial = tf.constant(0.1, shape=shape)
		return tf.Variable(initial)
		#return weight_variable(shape)

	def calculate(x, dropout = False):
		res = tf.matmul(x, weights[0]) + biases[0] #initial calculation for the first layer
		for i in range(hidden_layers):
			i+=1 #offset because we've done the first layer

			if activation == 'relu':
				print("Using relu activation")
				res = tf.nn.relu(res)

			if dropout and i == dropoutIndex:
				res = tf.nn.dropout(res, 0.5)
				print("Dropping on layer", i)

			res = tf.matmul(res, weights[i]) + biases[i]
		return res

	def l2_loss():
		res = 0.0
		for weight in weights:
			res += tf.nn.l2_loss(weight)
		return res

	global graph
	graph = tf.Graph()
	with graph.as_default():
		# Input data. For the training data, we use a placeholder that will be fed
		# at run time with a training minibatch.
		global tf_train_dataset
		tf_train_dataset = tf.placeholder(tf.float32,
							shape=(batch_size, image_width * image_height))
		global tf_train_labels
		tf_train_labels = tf.placeholder(tf.float32, shape=(batch_size, num_labels))
		tf_valid_dataset = tf.constant(dataset['valid'])
		tf_test_dataset = tf.constant(dataset['test'])

		global regularization
		regularization = tf.constant(0.0)#tf.placeholder(tf.float32)
		#dropoutIndex = tf.placeholder(tf.int32)

		# Variables.
		weights = []
		biases = []

		for x in range(hidden_layers+1):
			width = (image_width * image_height) if x is 0 else hidden_nodes[x-1]
			height = (num_labels) if x is hidden_layers else hidden_nodes[x]
			weights.append(weight_variable([width, height]) )
			biases.append(bias_variable([height]) )
			print("Created weights and biases with size %d and %f" % (width, height))

		# Training computation.
		logits = calculate(tf_train_dataset, True)
		global loss
		loss = tf.reduce_mean(
			tf.nn.softmax_cross_entropy_with_logits(labels=tf_train_labels, logits=logits)) * 3 + regularization*l2_loss()

		global_step = tf.Variable(0)  # count the number of steps taken.
		learning_rate = tf.train.exponential_decay(0.0001, global_step, 1001, 0.96)

		# Optimizer.
		global optimizer
		optimizer = tf.train.GradientDescentOptimizer(learning_rate).minimize(loss, global_step=global_step)

		# Predictions for the training, validation, and test data.
		global train_prediction
		train_prediction = tf.nn.softmax(logits)
		global valid_prediction
		valid_prediction = tf.nn.softmax(calculate(tf_valid_dataset))
		global test_prediction
		test_prediction = tf.nn.softmax(calculate(tf_test_dataset))

def run_train(dataset, labels, image_width, image_height, num_labels):
	batch_size = 128

	hidden_nodes = [2048, 1024, 300, 50]

	hidden_layers = 4

	activation = 'relu'

	dropoutIndex = 10

	reg_vals=[0]
	acc_vals = []

	num_steps = 10000

	num_batches = 999999999

	steps = []
	vals = []

	build_network(dataset, batch_size, image_width, image_height, num_labels, hidden_layers, hidden_nodes, dropoutIndex, activation)

	for reg_val in reg_vals:
		with tf.Session(graph=graph) as session:
			tf.global_variables_initializer().run()
			print("Initialized")
			for step in range(num_steps):
				# Pick an offset within the training data, which has been randomized.
				# Note: better randomization across epochs needed.
				offset = ((step % num_batches) * batch_size) % ( labels['train'].shape[0] - batch_size)
				# Generate a minibatch.
				batch_data = dataset['train'][offset:(offset + batch_size), :]
				batch_labels = labels['train'][offset:(offset + batch_size), :]
				# Prepare a dictionary telling the session where to feed the minibatch.
				# The key of the dictionary is the placeholder node of the graph to be fed,
				# and the value is the numpy array to feed to it.
				feed_dict = {tf_train_dataset : batch_data, tf_train_labels : batch_labels, regularization: reg_val}
				_, l, predictions = session.run([optimizer, loss, train_prediction], feed_dict=feed_dict)
				if (step % 500 == 0):
					print("Minibatch loss at step %d: %f" % (step, l))
					print("Minibatch accuracy: %.1f%%" % accuracy(predictions, batch_labels))
					print(len(predictions[predictions[:,0] > 0.5]), "_", len(predictions))
					val_pred = valid_prediction.eval()
					val = accuracy(val_pred, labels['valid'])
					print("Validation accuracy: %.1f%%" % val)
					print(len(val_pred[val_pred[:,0] > 0.5]), "_", len(val_pred))
					steps.append(step)
					vals.append(val)
			test_acc = accuracy(test_prediction.eval(), labels['test'])
			acc_vals.append(test_acc)
			print("Test accuracy: %.1f%%" % test_acc)

def accuracy(predictions, labels):
		return (100.0 * np.sum(np.argmax(predictions, 1) == np.argmax(labels, 1))
			/ predictions.shape[0])