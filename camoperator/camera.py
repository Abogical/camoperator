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
