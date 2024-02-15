import serial

class Controller:
    max=80000

    def __init__(self, port):
        self.serial_port = serial.Serial(port)
    
    def reset(self):
        pass

    def move_x(self, x):
        pass

    def move_y(self, x):
        pass

    def close(self, x):
        pass