class RequestsManager(dict):
    
    def __getitem__(self, key):
        if isinstance(key, list):
            key = tuple(key)
        if (not isinstance(key, tuple) 
            or len(key) != 2 
            or not isinstance(key[0], str) 
            or not isinstance(key[1], bool)):
            raise Exception("Invalid key")
        if not super().get(key):
            super().__setitem__(key, [])

        return super().__getitem__(key)

