import argparse
import os

import cv2
import numpy as np
import svgwrite

from utils import contrast, map_values


def to_tiles(file_in, file_out, invert=False,
             n_tiles_h=None, n_tiles_v=None,
             tile_type='circles', min_thick=0.1, min_tile_size=0., border=1.):
    """
    Reproduce an image with mosaic.

    Parameters
    ----------
    file_in : str
        Path of the input image.
    file_out : str
        Path of the output SVG image.
    invert : bool, optional
        Invert bright and dark values. (default : False)
    n_tiles_h : int, optional
        Number of tiles to use horizontally.
        (At least one of n_tiles_h and n_tiles_v must be provided)
    n_tiles_v : int, optional
        Number of tiles to use vertically.
        (At least one of n_tiles_h and n_tiles_v must be provided)
    tile_type : str, optional
        'circles' or 'squares'. (default : 'circles')
    min_thick : float, optional
        Minimum thickness of the bright grid, in ratio of a tile size. (default : 0.1)
        For normal results : min_thick in [0, 1], and min_thick + min_tile_size < 1
    min_tile_size : float, optional
        Minimum size of a tile, in ratio of a tile size. (default : 0.)
        For normal results : min_tile_size in [0, 1], and min_thick + min_tile_size < 1
    border : float, optional
        Border size around the generated svg, in ratio of a tile size. Choose 0 for no border. (default : 1.)
    """

    # Input as grayscale, and map to [0, 255].
    image = contrast(cv2.imread(file_in, 0), invert=invert)
    height_in, width_in = image.shape

    if n_tiles_h is None and n_tiles_v is None:
        raise AssertionError('Either n_tiles_h or n_tiles_v must be specified.')
    if n_tiles_v is None:
        n_tiles_v = round(n_tiles_h * height_in / width_in)
    if n_tiles_h is None:
        n_tiles_h = round(n_tiles_v * width_in / height_in)

    tile_width = width_in / n_tiles_h
    tile_height = height_in / n_tiles_v

    # Resize to nearest multiple, for equally sized tiles.
    width_out = round(tile_width) * n_tiles_h
    height_out = round(tile_height) * n_tiles_v
    image = cv2.resize(image, (width_out, height_out), interpolation=cv2.INTER_LINEAR)

    # Compute tile sizes, averaging over each area.
    values = image.reshape(n_tiles_v, height_out // n_tiles_v, n_tiles_h, width_out // n_tiles_h).mean(axis=(1, -1))

    # Array to be filled with the [[X, Y], [W, H]] elements of each tile.
    # value == 0. means largest tile, value == 255. means smallest tile.
    tiles = np.empty((n_tiles_v, n_tiles_h, 2, 2), dtype='float')
    # Tile centers
    tiles[:, :, 0, 0] = 0.5 + np.arange(n_tiles_h)
    tiles[:, :, 0, 1] = 0.5 + np.arange(n_tiles_v)[:, np.newaxis]
    # Merge to an array of tiles
    tiles = tiles.reshape(n_tiles_v * n_tiles_h, 2, 2)
    # Tile sizes
    tiles[:, 1] = map_values(values, 0., 255., 1. - min_thick, min_tile_size).reshape(n_tiles_v * n_tiles_h, 1)

    if tile_type.lower() in ['circle', 'circles']:
        # Radius is half the size
        tiles[:, 1] /= 2.
    elif tile_type.lower() in ['square', 'squares']:
        # X, Y must be upper-left corner
        tiles[:, 0] -= tiles[:, 1] / 2.
    else:
        raise NotImplementedError

    # Upscale to original dimensions
    tiles *= tile_width, tile_height

    # Frame
    border_h = border * tile_width
    border_v = border * tile_height
    tiles[:, 0] += border_h, border_v
    frame = np.zeros((4, 2), dtype='float')
    frame[1:3, 1] = height_in + 2. * border_v
    frame[2:4, 0] = width_in + 2. * border_h

    dwg = svgwrite.Drawing(file_out, profile='basic')

    if tile_type.lower() in ['square', 'squares']:
        draw_func = dwg.rect
    elif tile_type.lower() in ['circle', 'circles']:
        draw_func = dwg.ellipse
    else:
        raise NotImplementedError

    # Draw
    for tile in tiles:
        if tile[1].min() == 0.:
            continue
        dwg.add(draw_func(tile[0], tile[1], fill='#000000'))
    if border > 0.:
        # Draw frame
        dwg.add(dwg.polygon(points=frame, stroke='#000000', fill='none'))
    dwg.save(pretty=True)
    print('Output : {}'.format(file_out))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file-in', type=str, required=True,
                        help='Path of the input image.')
    parser.add_argument('--file-out', type=str, default=None,
                        help='Path of the output SVG image. (default : input file but it\'s SVG)')
    parser.add_argument('--invert', action='store_true',
                        help='Invert bright and dark values. (default : False)')
    parser.add_argument('--n-tiles-h', type=int, default=None,
                        help='Number of tiles to use horizontally.\n' +
                             '(At least one of n-tiles-h and n-tiles-v must be provided)')
    parser.add_argument('--n-tiles-v', type=int, default=None,
                        help='Number of tiles to use vertically.\n' +
                             '(At least one of n-tiles-h and n-tiles-v must be provided)')
    parser.add_argument('--tile-type', type=str, default='circles',
                        help="'circles' or 'squares'. (default : 'circles')")
    parser.add_argument('--min-thick', type=float, default=0.1,
                        help='Minimum thickness of the bright grid, in ratio of a tile size. (default : 0.1)\n' +
                             "For normal results : 'min-thick' in [0, 1], and 'min-thick' + 'min-tile-size' < 1")
    parser.add_argument('--min-tile-size', type=float, default=0.,
                        help='Minimum size of a tile, in ratio of a tile size. (default : 0.)\n' +
                             "For normal results : 'min-tile-size' in [0, 1], and 'min-thick' + 'min-tile-size' < 1")
    parser.add_argument('--border', type=float, default=1.,
                        help='Border size around the generated svg, in ratio of a tile size.\n' +
                             'Choose 0 for no border. (default : 1.)')
    args = parser.parse_args()

    if args.file_out is None:
        args.file_out = os.path.splitext(args.file_in)[0] + '_tiles.svg'
    elif os.path.splitext(args.file_out)[-1] != '.svg':
        args.file_out += '.svg'

    to_tiles(file_in=args.file_in, file_out=args.file_out, invert=args.invert,
             n_tiles_h=args.n_tiles_h, n_tiles_v=args.n_tiles_v, tile_type=args.tile_type,
             min_thick=args.min_thick, min_tile_size=args.min_tile_size, border=args.border)
