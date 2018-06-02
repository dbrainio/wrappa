class DSModel:

    def __init__(self, **kwargs):
        pass

    def predict(self, data):
        res = [[{'image': v['image'], 'text': 'Test dsjfkas'}, {
            'image': v['image'], 'text': 'Test dsjfkas'}] for v in data]
        return res
