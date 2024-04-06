'''
Copyright (C) 2024  Abdelrahman Abdelrahman

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''


import serial

class Controller:
    max = 128000

    def __init__(self, port):
        self.serial_port = serial.Serial(
            port,
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=40
        )
        
        # Check connection
        self.command(b"?R\r", b"?R\rOK\n")

        # Set maximum speed
        self.command(b"V255\r", b"V255\rOK\n")
        
    def command(self, request, expected_response):
        self.serial_port.write(request)
        response = self.serial_port.read(len(expected_response))
        if response != expected_response:
            raise RuntimeError(f"Serial Controller: Expected response {expected_response}. Got {response}")

    def reset(self):
        for axis in ["X", "Y"]:
            self.command(f"H{axis}0\r".encode('ascii'), f"H{axis}0\rOK\n".encode('ascii'))
        self.x = 0
        self.y = 0

    def move_x(self, dx):
        self.command(f"X{dx:+d}\r".encode('ascii'), f"X{dx:+d}\rOK\n".encode('ascii'))
        self.x += dx

    def move_y(self, dy):
        self.command(f"Y{dy:+d}\r".encode('ascii'), f"Y{dy:+d}\rOK\n".encode('ascii'))
        self.y += dy

    def close(self):
        self.serial_port.close()