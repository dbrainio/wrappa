class DSModel:

    def __init__(self, **kwargs):
        pass

    def predict(self, data):
        res = [[
            {
                'image': {
                    'payload': v['image'],
                    'ext': 'jpg'
                },
                'text': 'Test1',
            }, {
                'image': {
                    'payload': v['image'],
                    'ext': 'jpg'
                },
                'text': 'Test2',
            }] for v in data]
        return res
