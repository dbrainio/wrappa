from time import sleep
from wrappa import WrappaImage, WrappaText, WrappaObject


class DSModel:

    def __init__(self, **kwargs):
        pass

    def predict(self, data):
        res = []
        for v in data:

            img = WrappaImage.init_from_ndarray(**{
                'payload': v.image.as_ndarray,
                'ext': v.image.ext,
                'name': v.image.name
            })
            res.append(WrappaObject(img, WrappaText('Test1')))

        return res
