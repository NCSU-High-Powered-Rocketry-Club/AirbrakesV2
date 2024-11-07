import numpy as np

values = [1,2,3]
if any(value is None for value in values):
    raise AttributeError('test')
