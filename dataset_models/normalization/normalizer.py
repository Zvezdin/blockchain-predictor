import abc

class Normalizer(abc.ABC):
    def __init__(self, data):
        pass

    @abc.abstractmethod
    def transform(self, data):
        pass

    @abc.abstractmethod
    def inverse_transform(self, data):
        pass
