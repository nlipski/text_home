def getHelp():
    return "Don't be a bumbass"

def checkConfirm(message):
    txt = message.lower()
    if (txt == 'yes' or txt == 'y' or txt == 'ye' or txt == 'yea' or txt == 'oui' or txt == 'yup' or txt == 'yep'):
        return True
    else:
        return False

class storedLocationClass:
    def __init__(self, name, location):
        self.name = name
        self.location = location