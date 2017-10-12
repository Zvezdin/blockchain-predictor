import pandas as pd

from dataset_model import DatasetModel


class MatrixModel(DatasetModel):
    def __init__(self):
        self.name="matrix"
        self.requires=[]

    def generate(self, properties):
        data = pd.concat([prop.reset_index(drop=True) for prop in properties], axis=1).values

        #todo: Do sliding window to gen dataset.