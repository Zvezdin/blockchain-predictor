import abc

class Property:
    def __init__(self):
        self.name = ""

    @abc.abstractmethod
    def processTick(self, block, tx, course):
        """Takes block, transaction and course data for an interval and returns the property's value"""
    
