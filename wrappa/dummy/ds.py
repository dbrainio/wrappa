from time import sleep
from wrappa import WrappaImage, WrappaText, WrappaObject


class DSModel:

    def __init__(self, **kwargs):
        pass

    def predict(self, data, json):
        if json:
            return [[{
                'text': 'Test1'
            }, {
                'text': 'Тест2'
            }]]

        res = []
        for v in data:
            img = WrappaImage.init_from_ndarray({
                'payload': v.image.as_ndarray,
                'ext': v.image.ext
            })
            res.append([
                WrappaObject(img, WrappaText('Test1')),
                WrappaObject(v.image, WrappaText('Тест2'))
            ])

        return res
