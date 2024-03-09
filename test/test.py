import unittest
from unittest.mock import patch
import camoperator.main
import camoperator.camera
import camoperator.controller
import camoperator.calibrate
import os
import numpy as np
import random
import time
import re
import datetime
import shutil
import rawpy
import cv2
import io
import json
from dataclasses import dataclass
import tempfile
import logging

filename_re = re.compile("(\\d+)-(\\d+)\\.(.*)")
time_speed = 100

@dataclass
class MockCameraFile:
    folder: str
    name: str

    def __hash__(self):
        return hash((self.folder, self.name))

class BaseMockCamera:
    def __init__(self, config={}):
        self.mock_storage = {}

    def get_image(self):
        raise NotImplementedError

    def capture(self):
        time.sleep(2/time_speed)
        mock_filename = MockCameraFile('', datetime.datetime.now().isoformat())
        self.mock_storage[mock_filename] = self.get_image()
        return mock_filename
    
    def download(self, source, destination):
        time.sleep(1/time_speed)
        cv2.imwrite(destination, cv2.cvtColor(self.mock_storage[source], cv2.COLOR_RGB2BGR))
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

        logging.info("Moving x by %d to new position %d", dx, self.x)

        if self.x < 0:
            raise RuntimeError(f'x is set as negative ({self.x}) after command {dx}')
        if self.x > self.max:
            raise RuntimeError(f'x is set at a number higher than the maximum ({self.x}) after command {dx}')
    
    def move_y(self, dy):
        if not isinstance(dy, (int, np.integer)):
            raise RuntimeError(f'dx {dy} is not an integer')

        time.sleep(abs(dy)/(self.speed*25*time_speed))
        self.y = self.y+dy

        logging.info("Moving y by %d to new position %d", dy, self.y)

        if self.y < 0:
            raise RuntimeError(f'y is set as negative ({self.y}) after command {dy}')
        if self.y > self.max:
            raise RuntimeError(f'x is set at a number higher than the maximum ({self.y}) after command {dy}')

    def close(self):
        pass



class CLITest(unittest.TestCase):
    class MockConfigCamera(BaseMockCamera):
        def __init__(self, config={}):
            self.check_config(config)
            super().__init__(config)

    def setUp(self):
        self.example_path = os.path.join('test', '.artifacts', 'cli_test_output', datetime.datetime.now().isoformat())
        self.X = random.randint(5,10)
        self.Y = random.randint(5,10)
        self.min_x = random.randint(0, 10000)
        self.max_x = random.randint(BaseMockController.max-10000, BaseMockController.max)
        self.min_y = random.randint(0, 10000)
        self.max_y = random.randint(BaseMockController.max-10000, BaseMockController.max)
        self.config = {
            "f-number": random.uniform(3, 9),
            "whitebalance": random.randint(300, 1000),
            "iso": random.randint(100, 1000),
            "shutterspeed": f"1/{random.randint(10,20)}"
        }

        os.makedirs(self.example_path, exist_ok=True)

        with open(os.path.join(self.example_path, "config.json"), "w") as config_file:
            json.dump(self.config, config_file)
        
        self.MockConfigCamera.check_config = lambda _, config: self.assertDictEqual(config, self.config)

    def tearDown(self):
        try:
            shutil.rmtree(self.example_path)
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

        class MockCamera(self.MockConfigCamera):
            camera_height, camera_width = random.randint(400, 600), random.randint(400, 600) 
            def get_image(self):
                shape = (MockCamera.camera_height, MockCamera.camera_width)
                result = np.zeros((*shape, 3), dtype=np.uint8)
                result[:, :, 0] = MockController.instance.x % 256
                result[:, :, 1] = MockController.instance.y % 256
                result[:, :, 2] = np.random.randint(0, 256, shape)

                return result


        with patch("sys.argv", ['camoperator', self.example_path, '-p', 'COM4', '-X', str(self.X), '-Y', str(self.Y),
            '--min-x', str(self.min_x), '--max-x', str(self.max_x), '--min-y', str(self.min_y), '--max-y', str(self.max_y)]):
            with patch("camoperator.main.Controller", MockController):
                with patch("camoperator.main.Camera", MockCamera):
                    with patch("camoperator.main.get_filename", lambda directory, x, y: os.path.join(directory, f"{x}-{y}.png")):
                        camoperator.main.main()
        
        checked_files = np.zeros((self.X, self.Y))
        y_positions = np.round(np.linspace(self.min_y, self.max_y, self.Y))
        x_positions = np.round(np.linspace(self.max_x, self.min_x, self.X))
        for filename in os.listdir(self.example_path):
            if filename != 'config.json':
                match = filename_re.match(filename)
                self.assertIsNotNone(match, f'File {filename} does not match expected format')
                x, y = match.group(1,2)
                x, y = int(x), int(y)
                checked_files[x, y] = 1
                np_img = cv2.cvtColor(cv2.imread(os.path.join(self.example_path, filename)), cv2.COLOR_BGR2RGB)
                self.assertTrue((np_img[:,:, 0] == x_positions[x] % 256).all())
                self.assertTrue((np_img[:,:, 1] == y_positions[y] % 256).all())
                self.assertEqual(np_img.shape, (MockCamera.camera_height, MockCamera.camera_width, 3))
        
        self.assertTrue(checked_files.all())

    def test_resume_run(self):
        resume_x = random.randint(1, self.X-2)
        resume_y = random.randint(1, self.Y-2)

        logging.info('Starting test_resume_run with arguments %s',
        ['camoperator', self.example_path, '-p', 'COM4', '-X', str(self.X), '-Y', str(self.Y),
        '--min-x', str(self.min_x), '--max-x', str(self.max_x), '--min-y', str(self.min_y),  '--max-y', str(self.max_y),
            '--resume', f'{resume_x},{resume_y}'])

        class MockController(BaseMockController):
            def __init__(self, port):
                super().__init__(port)
                MockController.instance = self

        class MockCamera(self.MockConfigCamera):
            camera_height, camera_width = random.randint(400, 600), random.randint(400, 600) 
            def get_image(self):
                shape = (MockCamera.camera_height, MockCamera.camera_width)
                result = np.zeros((*shape, 3), dtype=np.uint8)
                result[:, :, 0] = MockController.instance.x % 256
                result[:, :, 1] = MockController.instance.y % 256
                result[:, :, 2] = np.random.randint(0, 256, shape)

                return result


        with patch("sys.argv", ['camoperator', self.example_path, '-p', 'COM4', '-X', str(self.X), '-Y', str(self.Y),
            '--min-x', str(self.min_x), '--max-x', str(self.max_x), '--min-y', str(self.min_y), '--max-y', str(self.max_y),
            '--resume', f'{resume_x},{resume_y}']):
            with patch("camoperator.main.Controller", MockController):
                with patch("camoperator.main.Camera", MockCamera):
                    with patch("camoperator.main.get_filename", lambda directory, x, y: os.path.join(directory, f"{x}-{y}.png")):
                        camoperator.main.main()
        
        checked_files = np.zeros((self.X, self.Y), dtype=bool)
        checked_files[:, :resume_y] = True
        if resume_y%2 == 0:
            checked_files[resume_x+1:, resume_y] = True
        else:
            checked_files[:resume_x, resume_y] = True

        y_positions = np.round(np.linspace(self.min_y, self.max_y, self.Y))
        x_positions = np.round(np.linspace(self.max_x, self.min_x, self.X))
        for filename in os.listdir(self.example_path):
            if filename != 'config.json':
                match = filename_re.match(filename)
                self.assertIsNotNone(match, f'File {filename} does not match expected format')
                x, y = match.group(1,2)
                x, y = int(x), int(y)

                self.assertFalse(checked_files[x, y])

                checked_files[x, y] = True
                np_img = cv2.cvtColor(cv2.imread(os.path.join(self.example_path, filename)), cv2.COLOR_BGR2RGB)
                self.assertTrue((np_img[:,:, 0] == x_positions[x] % 256).all())
                self.assertTrue((np_img[:,:, 1] == y_positions[y] % 256).all())
                self.assertEqual(np_img.shape, (MockCamera.camera_height, MockCamera.camera_width, 3))
        
        self.assertTrue(checked_files.all())

class CalibrateCLITest(unittest.TestCase):
    def test_empty(self):
        with self.assertRaises(SystemExit):
            camoperator.calibrate.main()
    
    def test_run(self):
        class MockController(BaseMockController):
            def __init__(self, port):
                super().__init__(port)
                MockController.instance = self

        class MockCamera(BaseMockCamera):
            def get_image(self):
                self.test_object.assertEqual(MockController.instance.x, 0)
                self.test_object.assertEqual(MockController.instance.y, 0)
                return None

            def download(self, source, destination):
                time.sleep(1/time_speed)
                shutil.copyfile('test/checkerboard.nef', destination)
                del self.mock_storage[source]

        MockCamera.test_object = self

        output_capture = io.TextIOWrapper(io.BytesIO())

        with patch('sys.argv', ['calibrate', '--checkerboard-dims', '8,6', '-p', 'COM4']):
            with patch('sys.stdout', output_capture):
                with patch("camoperator.calibrate.Controller", MockController):
                    with patch("camoperator.calibrate.Camera", MockCamera):
                        camoperator.calibrate.main()
        
        output_capture.seek(0)
        config = json.load(output_capture)
        self.assertIn("displayFOV", config)
        self.assertIn("f-number", config)
        self.assertIn("iso", config)
        self.assertIn("whitebalance", config)
        self.assertIn("shutterspeed", config)

            
