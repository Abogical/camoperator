# Camera operator

Operates the camera and controller to capture multiple images in the horizontal and vertical directions. These images collectively make up
the integral image.

## Install dependencies

Install dependencies first with `pip install -r requirements.txt`

## Usage

### Calibration
```
python3 -m camoperator.calibrate [-h] [-p CONTROLLER_PORT] --checkerboard-dims CHECKERBOARD_DIMS [--square-size SQUARE_SIZE] [-o OUTPUT]

Gets calibration information from the camera via capturing a checkerboard image.

options:
  -h, --help            show this help message and exit
  -p CONTROLLER_PORT, --controller-port CONTROLLER_PORT
                        Controller serial port. Will not move controller if not given.
  --checkerboard-dims CHECKERBOARD_DIMS
                        Checkerboard dimensions
  --square-size SQUARE_SIZE
                        Square size in meters
  -o OUTPUT, --output OUTPUT
                        Output filename, default is stdout
```
The configuration is a JSON file that is usually saved in the images folder where the capture process will store images to. The capture process will automatically read this config file if it is
found in the folder it saves to with the filename `config.json`. A checkerboard image needs to be in the photo with the checkerboard dimensions specified.

#### Example
```
python3 -m camoperator.calibrate -p /dev/ttyUSB0 -o ./images/config.json
```

### Capture
```
python3 -m camoperator.main [-h] -p CONTROLLER_PORT -X HORIZONTAL_IMAGES -Y VERTICAL_IMAGES [--min-x MIN_X] [--min-y MIN_Y] [--max-x MAX_X] [--max-y MAX_Y] [-c CONFIG] [--resume X,Y]
                   directory

Camera operator: Controls the camera arm rig to capture multiple images in the horizontal and vertical direction

positional arguments:
  directory             Directory to save images

options:
  -h, --help            show this help message and exit
  -p CONTROLLER_PORT, --controller-port CONTROLLER_PORT
                        Controller serial port
  -X HORIZONTAL_IMAGES, --horizontal-images HORIZONTAL_IMAGES
                        Number of horizontal images
  -Y VERTICAL_IMAGES, --vertical-images VERTICAL_IMAGES
                        Number of vertical images
  --min-x MIN_X         Minimum horizontal displacment
  --min-y MIN_Y         Minimum vertical displacment
  --max-x MAX_X         Maximum horizontal displacment
  --max-y MAX_Y         Maximum vertical displacment
  -c CONFIG, --config CONFIG
                        Camera configuration file
  --resume X,Y          Resume operation starting from a given image coordinates
```

## Demo in action
The following demo shows the camera operator taking 4x4 images. In practice this is scaled up to take images in the order of 100x100 or more.

https://github.com/Abogical/camoperator/assets/10688496/9f23de08-d4ea-428c-9323-c0a7fd4ac508

The following command is run in order to run this demo:
```
python3 -m camoperator.main -p /dev/ttyUSB0 -X 4 -Y 4 ./images/
```
