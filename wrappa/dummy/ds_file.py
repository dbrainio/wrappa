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
            res.append([
                WrappaObject(v.file, WrappaText('Test1')),
                WrappaObject(v.file, WrappaText('Тест2'))
            ])

        return res
