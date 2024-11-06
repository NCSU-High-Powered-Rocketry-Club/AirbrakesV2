import numpy as np
from scipy.spatial.transform import Rotation as R

reference_vector = np.array([0, 0.001, -0.999])

orientation = [-1, 0, 0]
rotation = R.from_quat([0.61057544, -0.34405011, -0.60791582, -0.37318307], scalar_first=True)
rotation, _ = R.align_vectors(
    [reference_vector],
    [orientation],
)
print(R.as_quat(rotation, scalar_first=True))
vec = rotation.apply(orientation)
print(vec)

orientation = [1, 0, 0]
rotation = R.from_quat([0.37394506, -0.59507751, 0.41232952, 0.57968295], scalar_first=True)
rotation, _ = R.align_vectors(
    [reference_vector],
    [orientation],
)
print(R.as_quat(rotation, scalar_first=True))
vec = rotation.apply(orientation)
print(vec)

orientation = [0, 0, -1]
rotation = R.from_quat([0.85752511, 0.02006555, 0.00998313, -0.51395386], scalar_first=True)
rotation, _ = R.align_vectors(
    [reference_vector],
    [orientation],
)
print(R.as_quat(rotation, scalar_first=True))
vec = rotation.apply(orientation)
print(vec)
