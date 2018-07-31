class DSModel:

    def __init__(self, **kwargs):
        pass

    def predict(self, data, json):
        if json:
            return [[{
                'text': 'Test1'
            }, {
                'text': 'Test2'
            }]]

        res = [[
            {
                'image': v['image'],
                'text': 'Test1',
            }, {
                'image': v['image'],
                'text': 'Test2',
            }] for v in data]
        return res
