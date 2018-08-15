from time import sleep


class DSModel:

    def __init__(self, **kwargs):
        pass

    def predict(self, data, json):
        # sleep(60)
        if json:
            return [[{
                'text': 'Test1'
            }, {
                'text': 'Тест2'
            }]]

        res = [[
            {
                'image': v['image'],
                'text': 'Test1',
            }, {
                'image': v['image'],
                'text': 'Тест2',
            }] for v in data]
        return res
