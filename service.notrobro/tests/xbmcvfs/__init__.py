import os


# this exists just to serve as placeholder for the real xbmcvfs available within Kodi at runtime for testing
def exists(file):
    return os.path.exists(file)


class File:
    filename = None

    def __init__(self, filename):
        self.filename = filename

    def read(self):
        result = None
        with open(self.filename, "r") as f:
            result = f.readlines()
        return ''.join(result) # xbmcvfs returns all lines as a single string

    def close(self):
        return True
