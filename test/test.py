import unittest
from unittest.mock import patch
import camoperator.main
import camoperator.camera
import camoperator.controller
import os
import numpy as np
from PIL import Image
import random
import time
import re
import datetime
import shutil

filename_re = re.compile("(\\d+)-(\\d+)\\.(.*)")
time_speed = 100

class BaseMockCamera:
    def __init__(self):
        self.mock_storage = {}

    def get_image(self):
        raise NotImplementedError

    def capture(self):
        time.sleep(2/time_speed)
        mock_filename = datetime.datetime.now().isoformat()
        self.mock_storage[mock_filename] = self.get_image()
        return mock_filename
    
    def download(self, source, destination):
        time.sleep(1/time_speed)
        Image.fromarray(self.mock_storage[source]).save(destination)
        del self.mock_storage[source]

    def close(self):
        pass


class BaseMockController:
    max = 80000

    def __init__(self, port):
        self.x = random.randint(0, 80000)
        self.y = random.randint(0, 80000)
        self.speed = random.randint(150, 255)

    def reset(self):
        self.move_x(-self.x)
        self.move_y(-self.y)
    
    def move_x(self, dx):
        if not isinstance(dx, (int, np.integer)):
            raise RuntimeError(f'dx {dx} is not an integer')
        
        time.sleep(abs(dx)/(self.speed*25*time_speed))
        self.x = self.x+dx
        if self.x < 0:
            raise RuntimeError(f'x is set as negative ({self.x}) after command {dx}')
    
    def move_y(self, dy):
        if not isinstance(dy, (int, np.integer)):
            raise RuntimeError(f'dx {dy} is not an integer')

        time.sleep(abs(dy)/(self.speed*25*time_speed))
        self.y = self.y+dy
        if self.y < 0:
            raise RuntimeError(f'y is set as negative ({self.y}) after command {dy}')

    def close(self):
        pass



class CLITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example_path = os.path.join('test', '.artifacts', 'cli_test_output', datetime.datetime.now().isoformat())
        cls.X = random.randint(5,10)
        cls.Y = random.randint(5,10)
        os.makedirs(cls.example_path, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        try:
            shutil.rmtree(cls.example_path)
        except FileNotFoundError:
            pass

    def test_empty(self):
        with self.assertRaises(SystemExit):
            camoperator.main.main()

    def test_run(self):

        class MockController(BaseMockController):
            def __init__(self, port):
                super().__init__(port)
                MockController.instance = self

        class MockCamera(BaseMockCamera):
            camera_height, camera_width = random.randint(400, 600), random.randint(400, 600) 
            def get_image(self):
                shape = (MockCamera.camera_height, MockCamera.camera_width)
                result = np.zeros((*shape, 3), dtype=np.uint8)
                result[:, :, 0] = (MockController.max-MockController.instance.x) % 256
                result[:, :, 1] = MockController.instance.y % 256
                result[:, :, 2] = np.random.randint(0, 256, shape)

                return result


        with patch("sys.argv", ['camoperator', self.example_path, '-p', 'COM4', '-X', str(self.X), '-Y', str(self.Y)]):
            with patch("camoperator.main.Controller", MockController):
                with patch("camoperator.main.Camera", MockCamera):
                    with patch("camoperator.main.get_filename", lambda directory, x, y: os.path.join(directory, f"{x}-{y}.png")):
                        camoperator.main.main()
        
        checked_files = np.zeros((self.X, self.Y))
        y_positions = np.round(np.linspace(0, MockController.max, self.Y))
        x_positions = np.round(np.linspace(0, MockController.max, self.X))
        for filename in os.listdir(self.example_path):
            match = filename_re.match(filename)
            self.assertIsNotNone(match, f'File {filename} does not match expected format')
            x, y = match.group(1,2)
            x, y = int(x), int(y)
            checked_files[x, y] = 1 
            with Image.open(os.path.join(self.example_path, filename)) as im:
                np_img = np.array(im)
                self.assertTrue((np_img[:,:, 0] == x_positions[x] % 256).all())
                self.assertTrue((np_img[:,:, 1] == y_positions[y] % 256).all())
                self.assertEqual(np_img.shape, (MockCamera.camera_height, MockCamera.camera_width, 3))
        
        self.assertTrue(checked_files.all())
            
