# Camera operator

Operates the camera and controller to capture multiple images in the horizontal and vertical directions. These images collectively make up
the integral image.

## Usage

```
python -m camoperator.main [-h] -p CONTROLLER_PORT -X HORIZONTAL_IMAGES -Y VERTICAL_IMAGES [--min-x MIN_X] [--min-y MIN_Y] [--max-x MAX_X] [--max-y MAX_Y] directory
```