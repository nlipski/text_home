import json

class storedLocationClass:
    def __init__(self, name, location):
        self.name = name
        self.location = location

defaultCustomLocations = json.dumps({'locations':[]})