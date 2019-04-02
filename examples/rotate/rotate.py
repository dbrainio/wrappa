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
            rotated_img = np.rot90(img)
            resp = WrappaObject(WrappaImage.init_from_ndarray(
                payload=rotated_img,
                ext=obj.image.ext,
            ))
            responses.append(resp)
        return responses

    def predict_180(self, data, **kwargs):
        _ = kwargs
        # Data is always an array of WrappaObjects
        responses = []
        for obj in data:
            img = obj.image.as_ndarray
            rotated_img = np.rot90(img)
            rotated_img = np.rot90(rotated_img)
            resp = WrappaObject(WrappaImage.init_from_ndarray(
                payload=rotated_img,
                ext=obj.image.ext,
            ))
            responses.append(resp)
        return responses