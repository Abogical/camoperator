import argparse
from .camera import Camera
from .controller import Controller
import os
from itertools import cycle
import numpy as np
from tqdm import tqdm
import threading
from .utils import positive_int
import json

argument_parser = argparse.ArgumentParser(
    prog='camoperator',
    description='Camera operator: Controls the camera arm rig to capture '
        'multiple images in the horizontal and vertical direction'
)

argument_parser.add_argument(
    'directory',
    type=str,
    help='Directory to save images'
)

argument_parser.add_argument(
    '-p', '--controller-port',
    type=str,
    help='Controller serial port',
    required=True
)

argument_parser.add_argument(
    '-X', '--horizontal-images',
    type=positive_int,
    help='Number of horizontal images',
    required=True
)

argument_parser.add_argument(
    '-Y', '--vertical-images',
    type=positive_int,
    help='Number of vertical images',
    required=True
)

argument_parser.add_argument(
    '--min-x',
    type=positive_int,
    help='Minimum horizontal displacment',
    default=0
)

argument_parser.add_argument(
    '--min-y',
    type=positive_int,
    help='Minimum vertical displacment',
    default=0
)

argument_parser.add_argument(
    '--max-x',
    type=positive_int,
    help='Maximum horizontal displacment',
    default=Controller.max
)

argument_parser.add_argument(
    '--max-y',
    type=positive_int,
    help='Maximum vertical displacment',
    default=Controller.max
)

argument_parser.add_argument(
    '-c', '--config',
    type=argparse.FileType('r'),
    help='Camera configuration file'
)

def get_steps(min, max, divisions):
    positions = np.round(np.linspace(min, max, divisions))
    return (positions[1:]-positions[:-1]).astype(int)

class DownloadThread(threading.Thread):
    def __init__(self, camera, source, destination, progress):
        threading.Thread.__init__(self)
        self.camera = camera
        self.source = source
        self.destination = destination
        self.progress = progress
    
    def run(self):
        self.camera.download(self.source, self.destination)
        self.progress.update(1)

def get_filename(directory, x, y):
    return os.path.join(directory, f"{x}-{y}.nef")

download_thread = None
def capture_xy(camera, directory, x, y, progress):
    global download_thread
    if download_thread != None:
        download_thread.join()

    progress.set_description(f'Capturing images. Current ({x}, {y})')
    capture_file = camera.capture()
    download_thread = DownloadThread(
        camera,
        capture_file,
        get_filename(directory, x, y),
        progress
    )
    download_thread.start()

def capture_x_axis(camera, directory, y, x_steps, max_x, controller, progress):
    even_y = (y%2 == 0)
    
    capture_xy(camera, directory, max_x if even_y else 0, y, progress)

    for x, x_step in (zip(range(max_x-1, -1, -1), x_steps) if even_y else enumerate(reversed(-x_steps), start=1)):
        controller.move_x(x_step)
        capture_xy(camera, directory, x, y, progress)

def main():
    arguments = argument_parser.parse_args()
    controller = Controller(arguments.controller_port)

    # Get camera config if any
    camera_config = {}
    if arguments.config is not None:
        camera_config = json.load(arguments.config)
    else:
        try:
            with open(os.path.join(arguments.directory, 'config.json')) as camera_config_file:
                camera_config = json.load(camera_config_file)
        except FileNotFoundError:
            pass

    camera = Camera(dict(
        (key, camera_config[key])
        for key in camera_config
        if key in set(["f-number", "iso", "shutterspeed", "whitebalance"])
    ))
    
    controller.reset()

    if arguments.min_x > 0:
        controller.move_x(arguments.min_x)
    
    if arguments.min_y > 0:
        controller.move_y(arguments.min_y)

    y_steps = get_steps(arguments.min_y, arguments.max_y, arguments.vertical_images)
    x_steps = get_steps(arguments.min_x, arguments.max_x, arguments.horizontal_images)

    progress = tqdm(desc='Capturing images.', total=(arguments.horizontal_images)*(arguments.vertical_images))

    capture_x_axis(camera, arguments.directory, 0, x_steps, arguments.horizontal_images-1, controller, progress)
    for y, y_step in enumerate(y_steps, start=1):
        controller.move_y(y_step)
        capture_x_axis(camera, arguments.directory, y, x_steps, arguments.horizontal_images-1, controller, progress)
    
    download_thread.join()
    camera.close()
    controller.close()
        
        

if __name__ == "__main__":
    main()