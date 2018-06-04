class DSModel:

    def __init__(self, **kwargs):
        pass

    def predict(self, data):
        res = [[
            {
                'image': v['image'],
                'text': 'Test1',
            }, {
                'image': v['image'],
                'text': 'Test2',
            }] for v in data]
        return res
