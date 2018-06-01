class DSModel:

    def __init__(self, **kwargs):
        pass

    def predict(self, data):
        res = [{'image': v, 'text': 'Test dsjfkas'} for v in data]
        return res
