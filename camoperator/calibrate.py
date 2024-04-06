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


import argparse
from .controller import Controller
from .camera import Camera
from .utils import positive_int, dimensions
import tempfile
import os
import rawpy
import cv2
import exifread
import numpy as np
import json
import sys

argument_parser = argparse.ArgumentParser(
    prog='calibrate',
    description='Gets calibration information from the camera via capturing a checkerboard image.'
)

argument_parser.add_argument(
    '-p', '--controller-port',
    type=str,
    help='Controller serial port. Will not move controller if not given.',
)

argument_parser.add_argument(
    '--checkerboard-dims',
    type=dimensions,
    help='Checkerboard dimensions',
    required=True
)

argument_parser.add_argument(
    '--square-size',
    type=float,
    help='Square size in meters',
    default=1
)

argument_parser.add_argument(
    '-o', '--output',
    type=argparse.FileType(mode='w'),
    help='Output filename, default is stdout'
)

def main():
    arguments = argument_parser.parse_args()
    controller = Controller(arguments.controller_port) if arguments.controller_port else None
    camera = Camera({
        "autofocus": "On"
    })

    # Reset to origin
    if controller:
        controller.reset()

    # Take photo
    camera_file = camera.capture()
    _, extension = os.path.splitext(camera_file.name)
    handle, temp_filename = tempfile.mkstemp(extension, "camoperator")
    os.close(handle)
    camera.download(camera_file, temp_filename)

    with open(temp_filename, 'rb') as temp_file:
        if extension.lower() == ".nef":
            with rawpy.imread(temp_file) as raw_img:
                img = cv2.cvtColor(raw_img.postprocess(), cv2.COLOR_RGB2GRAY)
        else:
            img = cv2.imread(temp_filename, cv2.IMREAD_GRAYSCALE)
    
        exif_data = exifread.process_file(temp_file)
    os.remove(temp_filename)

    # Get calibration information
    ret, corners = cv2.findChessboardCorners(img, arguments.checkerboard_dims, None)
    if not ret:
        raise RuntimeError('No Checkerboard found')

    corners = cv2.cornerSubPix(img, corners, (11,11), (-1, -1), (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
    
    square_size = arguments.square_size
    objp = np.zeros((arguments.checkerboard_dims[0] * arguments.checkerboard_dims[1],3), np.float32)
    objp[:,:2] = np.mgrid[0:arguments.checkerboard_dims[0],0:arguments.checkerboard_dims[1]].T.reshape(-1,2) * square_size
    
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera([objp], [corners], (img.shape[1], img.shape[0]), None, None)
    f_number = float(exif_data["EXIF FNumber"].values[0])
    fov_x, fov_y, focal_length, _, _ = cv2.calibrationMatrixValues(mtx, (img.shape[1], img.shape[0]), f_number, f_number)

    output_buffer = arguments.output or sys.stdout
    json.dump(
        {
            "displayFOV": [fov_x, fov_y],
            "f-number": f"{f_number:.1f}",
            "whitebalance": exif_data['EXIF WhiteBalance'].values[0],
            "iso": exif_data['EXIF ISOSpeedRatings'].values[0],
            "shutterspeed": str(exif_data["EXIF ExposureTime"].values[0])
        },
        output_buffer
    )


if __name__ == "__main__":
    main()
