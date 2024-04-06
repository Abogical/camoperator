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


import gphoto2 as gp
import os

class Camera:
    def __init__(self, config={}):
        self.camera = gp.Camera()
        self.camera.init()

        # Set up config
        # TODO: make this modifiable
        conf = self.camera.get_config()
        for key, value in {
            "imagequality": "NEF (Raw)",
            "autofocus": "Off",
            "capturemode": "Single Shot",
            **config
        }.items():
            conf.get_child_by_name(key).set_value(str(value))
        self.camera.set_config(conf)

    
    def capture(self):
        return self.camera.capture(gp.GP_CAPTURE_IMAGE)

    def download(self, source, destination):
        camera_file = self.camera.file_get(source.folder, source.name, gp.GP_FILE_TYPE_NORMAL)
        camera_file.save(destination)
        self.camera.file_delete(source.folder, source.name)

    def close(self):
        self.camera.exit()
