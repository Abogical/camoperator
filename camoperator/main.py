import argparse
from .camera import Camera
from .controller import Controller
import os
from itertools import cycle
import numpy as np
from tqdm import tqdm
import threading

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
    type=int,
    help='Number of horizontal images',
    required=True
)

argument_parser.add_argument(
    '-Y', '--vertical-images',
    type=int,
    help='Number of vertical images',
    required=True
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
    
    progress.set_description(f'Capturing images. Current (0, {y})')
    capture_xy(camera, directory, 0 if even_y else max_x, y, progress)

    for x, x_step in (enumerate(x_steps, start=1) if even_y else zip(range(max_x-1, -1, -1), reversed(-x_steps))):
        controller.move_x(x_step)
        progress.set_description(f'Capturing images. Current ({x}, {y})')
        capture_xy(camera, directory, x, y, progress)

def main():
    arguments = argument_parser.parse_args()
    controller = Controller(arguments.controller_port)
    camera = Camera()
    
    controller.reset()

    y_steps = get_steps(0, Controller.max, arguments.vertical_images)
    x_steps = get_steps(0, Controller.max, arguments.horizontal_images)

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