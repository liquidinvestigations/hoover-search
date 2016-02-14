class Loader:

    label = "Upload"

    def __init__(self, **config):
        self.config = config

    def get_metadata(self):
        return self.config
