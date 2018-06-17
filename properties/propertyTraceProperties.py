import sys, os
import math

sys.path.insert(0, os.path.realpath('property_util'))

from blockchain_state import state
from movingAverages import average
from movingAverages import Average

from .property import Property

class PropertyTraceProperties(Property):
	def __init__(self):
		super().__init__()
		self.name = "propertyTraceProperties"
		self.requiresState = True
		self.requires = [] #the rest should be required by the state
		self.provides = ["traceTx",
			"traceBl",
			"topXCount",
			"volumeLeavingTopX",
			"volumeEnteringTopX",
			"avgGasByTopX",
			"avgVal",
			"avgValToTopX",
			"avgValFromTopX",
			"avgValToNew",
			"avgValFromRecent",
			"tracesFromRecent",
			"shareTracesFromRecent",
			"gasUsedByNew",
			"avgGasUsed",
			"avgBalOfRecent",
			"avgBalOfLocal",
			"avgBalOfRecent",
			"activeAccounts",
			"activeAccountsShare",
			"recentAccounts"]

		for el in self.provides:
			#initialize multiple state variables that are named
			#after what is provided. The returned result from processTtick
			#uses this state
			setattr(self, el, 0)

	def processTick(self, data):
		blockCount = len(state.isBlock)
		txCount = len(state.isTransaction)
		traceCount = data['trace'].shape[0]

		fromI = data['trace'].columns.get_loc('from')+1

		self.traceTx = 0 if txCount is 0 else traceCount / txCount
		self.traceBl = 0 if traceCount is 0 else traceCount / blockCount
		
		self.topXCount = self.scale(len(state.topX))
		
		avgGasByTopXObj = Average()
		volumeLeavingTopX = 0
		volumeEnteringTopX = 0
		for acc in state.topX:
			avgGasByTopXObj.add(state.gasUsedBy.get(acc, 0))
			volumeLeavingTopX += state.amountSentBy.get(acc, 0)
			volumeEnteringTopX += state.amountReceivedBy.get(acc, 0)

		self.volumeLeavingTopX = self.scale(volumeLeavingTopX)
		self.volumeEnteringTopX = self.scale(volumeEnteringTopX)

		self.avgGasByTopX = self.scale(avgGasByTopXObj.get())

		avgValToTopXObj = Average()
		avgValFromTopXObj = Average()
		avgValObj = Average()
		avgValToNewObj = Average()
		tracesFromRecent = 0
		valFromRecentObj = Average()
		gasUsedByNewObj = Average()
		gasUsedObj = Average()

		for trace in data['trace'].itertuples():
			value = int(trace.value, 0)

			send = getattr(trace, '_'+str(fromI))
			recv = trace.to
			try:
				gas = int(trace.gasUsed, 0)
			except TypeError:
				gas = None
			
			if state.isTopX.get(send, False):
				avgValFromTopXObj.add(value)
			if state.isTopX.get(recv, False):
				avgValToTopXObj.add(value)
			if state.isAccountNew.get(send, False):
				gasUsedByNewObj.add(state.gasUsedBy.get(send, 0))
			for acc in [send, recv]:
				if state.isAccountNew.get(acc, False):
					avgValToNewObj.add(value)
			if state.isRecentlyCreated.get(send, False):
				tracesFromRecent += 1
				valFromRecentObj.add(value)
			
			avgValObj.add(value)

			if gas is not None:
				gasUsedObj.add(gas)

		self.avgVal = self.scale(avgValObj.get())
		self.avgValToTopX = self.scale(avgValToTopXObj.get())
		self.avgValFromTopX = self.scale(avgValFromTopXObj.get())
		self.avgValToNew = self.scale(avgValToNewObj.get())
		self.avgValFromRecent = self.scale(valFromRecentObj.get())
		self.tracesFromRecent = self.scale(tracesFromRecent)
		self.shareTracesFromRecent = 0 if traceCount is 0 else tracesFromRecent / traceCount
		self.gasUsedByNew = self.scale(gasUsedByNewObj.get())
		self.avgGasUsed = self.scale(gasUsedObj.get())

		balOfRecentObj = Average()
		for acc in state.recentlyCreated:
			balOfRecentObj.add(state.balances[acc])

		self.avgBalOfRecent = self.scale(balOfRecentObj.get())

		balOfLocalObj = Average()
		for acc in state.localAccounts:
			balOfLocalObj.add(state.balances[acc])
		self.avgBalOfLocal = self.scale(balOfLocalObj.get())

		self.activeAccounts = self.scale(len(state.localAccounts))
		#scaled by a hundred so it isn't too much of a small fraction
		self.activeAccountsShare = (self.activeAccounts * 100) / state.totalAccountsAmount
		self.recentAccounts = self.scale(len(state.recentlyCreated))


		return self.getRes()

	def getRes(self):
		vals = []
		for f in self.provides:
			val = getattr(self, f)
			vals.append(val)

		return vals

	def scale(self, val):
		if val <= 0:
			return val
		return math.log(val)