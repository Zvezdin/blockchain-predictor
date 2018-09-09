from .postprocessor import Postprocessor


class PostprocessorRelative(Postprocessor):

	def __init__(self):
		super().__init__()

		self.name = "%s_rel"
		self.previousTicks = 1

	def calculateAction(self, data):
		return data[1] - data[0]