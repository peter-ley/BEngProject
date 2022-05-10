class Module:
    def __init__(self, address):
        self._address = address

    def getIP(self):
        return(self._address)

class WheelModule(Module):
    def moveWheel(self, direction):
        print("Wheel moving "+direction)
    
class SensorModule(Module):
    pass
