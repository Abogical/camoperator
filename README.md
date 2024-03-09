# Camera operator

Operates the camera and controller to capture multiple images in the horizontal and vertical directions. These images collectively make up
the integral image.

## Usage

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