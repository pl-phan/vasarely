# vasarely
A standalone python to reproduce the style of Victor Vasarely in this artwork:

<img src="http://golem13.fr/wp-content/uploads/2019/02/Vasarely-expo-CentrePoimpidou.jpg" height="250">

(Found in the entrance hall of the Centre Pompidou in Paris.)

The code produces SVG images.

## Usage

### Bands
```
python bands.py --file-in images/test1.png --n-bands 40
python bands.py --file-in images/test2.png --n-bands 60
python bands.py --file-in images/test3.png --n-bands 50 --axis 0
```
Input (any) | Output (SVG)
:---: | :---:
<img src="images/test1.png" width="250">| <a href="images/test1_bands.svg"> <img src="images/test1_bands.png" width="250"> <a/>
<img src="images/test2.png" width="380">| <a href="images/test2_bands.svg"> <img src="images/test2_bands.png" width="380"> <a/>
<img src="images/test3.png" width="200">| <a href="images/test3_bands.svg"> <img src="images/test3_bands.png" width="200"> <a/>

```
usage: bands.py [-h] --file-in FILE_IN [--file-out FILE_OUT] [--invert]
                [--n-bands N_BANDS] [--axis AXIS] [--resolution RESOLUTION]
                [--min-thick MIN_THICK] [--min-space MIN_SPACE]
                [--border BORDER]

optional arguments:
  -h, --help            show this help message and exit
  --file-in FILE_IN     Path of the input image.
  --file-out FILE_OUT   Path of the output SVG image. (default : input file
                        but it's SVG)
  --invert              Invert bright and dark values. (default : False)
  --n-bands N_BANDS     Number of shadow bands to use. (default : 32)
  --axis AXIS           1 for vertical bands, 0 for horizontal bands. (default
                        : 1)
  --resolution RESOLUTION
                        Resolution of each band. (default : 320)
  --min-thick MIN_THICK
                        Minimum thickness of a bright band, in ratio of a band
                        width. (default : 0.1)
  --min-space MIN_SPACE
                        Minimum space between adjacent bright bands, in ratio
                        of a band width. (default : 0.1)
  --border BORDER       Border size around the generated svg, in ratio of a
                        band width. Choose 0 for no border. (default : 1.)
```

### Tiles
```
python tiles.py --file-in images/test1.png --n-tiles-h 50
python tiles.py --file-in images/test2.png --n-tiles-v 25
python tiles.py --file-in images/test3.png --n-tiles-h 50 --tile-type square
```
Input (any) | Output (SVG)
:---: | :---:
<img src="images/test1.png" width="250">| <a href="images/test1_tiles.svg"> <img src="images/test1_tiles.png" width="250"> <a/>
<img src="images/test2.png" width="380">| <a href="images/test2_tiles.svg"> <img src="images/test2_tiles.png" width="380"> <a/>
<img src="images/test3.png" width="200">| <a href="images/test3_tiles.svg"> <img src="images/test3_tiles.png" width="200"> <a/>

```
usage: tiles.py [-h] --file-in FILE_IN [--file-out FILE_OUT] [--invert]
                [--n-tiles-h N_TILES_H] [--n-tiles-v N_TILES_V]
                [--tile-type TILE_TYPE] [--min-thick MIN_THICK]
                [--min-tile-size MIN_TILE_SIZE] [--border BORDER]

optional arguments:
  -h, --help            show this help message and exit
  --file-in FILE_IN     Path of the input image.
  --file-out FILE_OUT   Path of the output SVG image. (default : input file
                        but it's SVG)
  --invert              Invert bright and dark values. (default : False)
  --n-tiles-h N_TILES_H
                        Number of tiles to use horizontally. (At least one of
                        n-tiles-h and n-tiles-v must be provided)
  --n-tiles-v N_TILES_V
                        Number of tiles to use vertically. (At least one of
                        n-tiles-h and n-tiles-v must be provided)
  --tile-type TILE_TYPE
                        'circles' or 'squares'. (default : 'circles')
  --min-thick MIN_THICK
                        Minimum thickness of the bright grid, in ratio of a
                        tile size. (default : 0.1) For normal results : 'min-
                        thick' in [0, 1], and 'min-thick' + 'min-tile-size' <
                        1
  --min-tile-size MIN_TILE_SIZE
                        Minimum size of a tile, in ratio of a tile size.
                        (default : 0.) For normal results : 'min-tile-size' in
                        [0, 1], and 'min-thick' + 'min-tile-size' < 1
  --border BORDER       Border size around the generated svg, in ratio of a
                        tile size. Choose 0 for no border. (default : 1.)
```
