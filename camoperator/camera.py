import gphoto2 as gp
import rawpy
import tempfile
import os
from PIL import Image

class Camera:
    def __init__(self):
        self.camera = gp.Camera()
        self.camera.init()
    
    def capture(self):
        return self.camera.capture()

    def download(self, source, destination):
        camera_file = self.camera.file_get(source.folder, source.file, gp.GP_FILE_TYPE_NORMAL)
        
        with tempfile.NamedTemporaryFile(delete_on_close=False) as fp:
            fp.close()
            camera_file.save(fp.name, mode='wb')
            Image.fromarray(rawpy.imread(fp.name).postprocess()).save(destination)
            os.remove(fp.name)
            
        self.camera.file_delete(source.folder, source.file)

    def close(self):
        self.camera.exit()