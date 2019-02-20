import numpy as np
from PIL import Image
from wrappa import WrappaObject, WrappaImage


class DSModel:

    def __init__(self, **kwargs):
        pass

    def predict(self, data, **kwargs):
        _ = kwargs
        responses = []
        # Here data is an array of WrappaObjects arrays
        for obj in data:
            imgs = list(map(lambda x: Image.fromarray(x.image.as_ndarray), obj))
            min_shape = sorted([(np.sum(i.size), i.size) for i in imgs])[0][1]
            imgs_comb = np.hstack((np.asarray(i.resize(min_shape)) for i in imgs))
            resp = WrappaObject(WrappaImage.init_from_ndarray(
                payload=imgs_comb,
                ext='jpg',
            ))
            responses.append(resp)
        return responses
