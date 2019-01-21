import numpy as np

from wrappa import WrappaObject, WrappaImage


class DSModel:

    def __init__(self, **kwargs):
        pass

    def predict(self, data, **kwargs):
        _ = kwargs
        # Data is always an array of WrappaObjects
        responses = []
        for obj in data:
            img = obj.image.as_ndarray
            resp = []
            for _ in range(4):
                rotated_img = np.rot90(img)
                _resp = WrappaObject(WrappaImage.init_from_ndarray(
                    payload=rotated_img,
                    ext=obj.image.ext,
                ))
                resp.append(_resp)
                img = rotated_img
            responses.append(resp)
        return responses
