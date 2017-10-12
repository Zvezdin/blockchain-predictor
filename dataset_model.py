import abc

class DatasetModel:
	"""An abstract class that is inherited by all dataset models."""

	def __init__(self):
			self.name = ""
			self.requires = []

	@abc.abstractmethod
	def generate(self, properties):
		"""Generates a dataset using the properties provided"""