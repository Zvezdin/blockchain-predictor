from neural_network import NeuralNetwork

import numpy as np
import tensorflow as tf

class CustomDeepNetwork(NeuralNetwork):
	def __init__(self):
		self.name="CustomDeepTf"

	def train(self, givenDataset, givenLabels, args = {}):
		dataset = {}
		labels = {}

		image_width = givenDataset['train'].shape[2]
		image_height = givenDataset['train'].shape[1]
		num_labels = 1


		for kind in ['train', 'valid', 'test']:
			print("Reformatting dataset with shape", givenDataset[kind].shape)
			dataset[kind], labels[kind] = self.labelsReformat(givenDataset[kind], givenLabels[kind], image_width, image_height, num_labels)
			print(kind, 'set', dataset[kind].shape, labels[kind].shape)
			print("Labels", givenLabels[kind][:5], labels[kind][:5])
			print("Neg: %.1f%%" % (100.0 - 100.0 * np.sum(givenLabels[kind]) / len(givenLabels[kind])) )

		print(labels)

		run_train(dataset, labels, image_width, image_height, num_labels)

	def predict(self, dataset):
		return predict()

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
			tf.nn.sigmoid_cross_entropy_with_logits(labels=tf_train_labels, logits=logits)) + regularization*l2_loss()

		#loss = tf.nn.l2_loss(tf.nn.sigmoid(logits) - tf_train_labels)

		global_step = tf.Variable(0)  # count the number of steps taken.
		learning_rate = tf.train.exponential_decay(0.001, global_step, 1001, 0.96)

		print("Shape of logits:")
		print(logits.shape, tf_train_labels.shape)

		# Optimizer.
		global optimizer
		optimizer = tf.train.GradientDescentOptimizer(learning_rate).minimize(loss, global_step=global_step)

		# Predictions for the training, validation, and test data.
		global train_prediction
		train_prediction = tf.nn.sigmoid(logits)
		global valid_prediction
		valid_prediction = tf.nn.sigmoid(calculate(tf_valid_dataset))
		global test_prediction
		test_prediction = tf.nn.sigmoid(calculate(tf_test_dataset))

#or 'binary'
OUTPUT_TYPE = "full"

test_results = None

def run_train(dataset, labels, image_width, image_height, num_labels):
	batch_size = 2

	hidden_nodes = [2048, 1024, 512, 50]

	hidden_layers = 4

	activation = 'relu'

	dropoutIndex = 1

	reg_vals=[0]
	acc_vals = []

	num_steps = 50001

	num_batches = 999999999

	steps = []
	vals = []

	build_network(dataset, batch_size, image_width, image_height, num_labels, hidden_layers, hidden_nodes, dropoutIndex, activation)

	for reg_val in reg_vals:
		with tf.Session(graph=graph) as session:
			tf.global_variables_initializer().run()
			print("Initialized")
			try:
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
						print("Minibatch accuracy: %.5f%% w_pos %.1f%% w_neg %.1f%%" % accuracy(predictions, batch_labels))
						print(len(predictions[predictions > 0.5]), "_", len(predictions))
						val_pred = valid_prediction.eval()
						val, pos, neg = accuracy(val_pred, labels['valid'])
						print("Validation accuracy: %.5f%% w_pos %.1f%% w_neg %.1f%%" % (val, pos, neg))
						print(len(val_pred[val_pred > 0.5]), "_", len(val_pred))
						steps.append(step)
						vals.append(val)
			except KeyboardInterrupt:
				print("Got interrupt at step %d. Stopping training..." % step)
			global test_results
			test_results = test_prediction.eval()

			test_acc, pos, neg = accuracy(test_results, labels['test'])
			acc_vals.append(test_acc)
			print("Test accuracy: %.5f%% w_pos %.1f%% w_neg %.1f%%" % (test_acc, pos, neg))

def predict():
	return test_results

def accuracy(predictions, labels):
		#this was used with softmax activation
		#return (100.0 * np.sum(np.argmax(predictions, 1) == np.argmax(labels, 1))
		#	/ predictions.shape[0])

		if OUTPUT_TYPE == 'binary':
			intersection = np.round(predictions) == labels
			print(predictions[:5], labels[:5])
			print(np.sum(intersection), predictions.shape[0])
			acc = 100 * np.sum(intersection) / predictions.shape[0]
			wrong_pos = 0
			wrong_neg = 0

			for i, res in enumerate(intersection): #for each correctness of returned result
				if not res: #if the prediction is not correct
					if not labels[i]: #count wrong positives or negatives
						wrong_pos +=1
					else:
						wrong_neg +=1

			wrong_pos /= predictions.shape[0] / 100 #turn to %
			wrong_neg /= predictions.shape[0] / 100
			return (acc, wrong_pos, wrong_neg)

		elif OUTPUT_TYPE == 'full':
			totalLoss = 0.0
			nullModelLoss = 0.0
			wrong_pos = 0
			wrong_neg = 0
			
			for i, res in enumerate(predictions):
				totalLoss += pow(abs(res - labels[i]), 1)

				nullModelLoss += pow((0.5 - labels[i]), 2)
				if res >= labels[i]:
					wrong_pos += 1
				else:
					wrong_neg += 1

			print("totalLoss is %4f" % totalLoss)

			#Note: nullModelLoss is not really suitable for this
			#totalLoss /= nullModelLoss
			totalLoss /= predictions.shape[0]
			wrong_pos /= predictions.shape[0] / 100.0 #turn to %
			wrong_neg /= predictions.shape[0] / 100.0
			return (totalLoss, wrong_pos, wrong_neg)

