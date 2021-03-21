import argparse
import os

import cv2
import numpy as np
import svgwrite

from utils import contrast, map_values


def to_tiles(file_in, file_out, invert=False, n_tiles_horizontal=None, n_tiles_vertical=None,
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
    n_tiles_horizontal : int, optional
        Number of tiles to use horizontally.
    n_tiles_vertical : int, optional
        Number of tiles to use vertically.
    tile_type : str, optional
        'squares' or 'circles'. (default : 'circles')
    min_thick : float, optional
        Minimum thickness of the bright grid, in ratio of a tile size. (default : 0.1)
    min_tile_size : float, optional
        Minimum size of the tiles, in ratio of a tile size. (default : 0.)
    border : float, optional
        Border size around the generated svg, in ratio of a tile size. (default : 1.)
    """

    # Input as grayscale, and map to [0, 255].
    image = contrast(cv2.imread(file_in, 0), invert=invert)
    height_in, width_in = image.shape

    if n_tiles_horizontal is None and n_tiles_vertical is None:
        raise AssertionError('Either n_tiles_horizontal or n_tiles_vertical must be specified.')
    if n_tiles_vertical is None:
        n_tiles_vertical = round(n_tiles_horizontal * height_in / width_in)
    if n_tiles_horizontal is None:
        n_tiles_horizontal = round(n_tiles_vertical * width_in / height_in)

    # Resize to nearest multiple, for equally sized tiles.
    tile_width = round(width_in / n_tiles_horizontal)
    width_out = tile_width * n_tiles_horizontal
    tile_height = round(height_in / n_tiles_vertical)
    height_out = tile_height * n_tiles_vertical

    image = cv2.resize(image, (width_out, height_out), interpolation=cv2.INTER_LINEAR)
    scale_factor_horizontal = width_out / width_in
    scale_factor_vertical = height_out / height_in

    # Convert in tile_size unit to px.
    min_thick *= 0.5 * (tile_width + tile_height)
    min_tile_size *= 0.5 * (tile_width + tile_height)
    border *= 0.5 * (tile_width + tile_height)

    # Compute tile sizes, with mean over each area.
    values = image.reshape(
        n_tiles_vertical, height_out // n_tiles_vertical,
        n_tiles_horizontal, width_out // n_tiles_horizontal
    ).mean(axis=(1, 3))

    tiles = np.empty((n_tiles_vertical, n_tiles_horizontal, 4), dtype='float')
    # Array will be filled with the coordinates for the (X, Y, W, H) elements of each tile.

    # Tile centers
    tiles[:, :, 0] = ((np.arange(n_tiles_horizontal) + 0.5) * tile_width / scale_factor_horizontal)[np.newaxis, :]
    tiles[:, :, 1] = ((np.arange(n_tiles_vertical) + 0.5) * tile_height / scale_factor_vertical)[:, np.newaxis]

    # Tile sizes
    tiles[:, :, 2] = map_values(values, 0., 255., tile_width / scale_factor_horizontal - min_thick, min_tile_size)
    tiles[:, :, 3] = map_values(values, 0., 255., tile_height / scale_factor_vertical - min_thick, min_tile_size)

    if tile_type.lower() in ['square', 'squares']:
        # X, Y must be upper-left corner
        tiles[:, :, :2] -= tiles[:, :, 2:] / 2.
    elif tile_type.lower() in ['circle', 'circles']:
        # Radius is half th size
        tiles[:, :, 2:] /= 2.
    else:
        raise NotImplementedError

    # Offset both x and y
    tiles[:, :, :2] += border

    # Frames corners
    frame = np.zeros((4, 2), dtype='float')
    frame[1:3, 1] = height_in + 2. * border
    frame[2:4, 0] = width_in + 2. * border

    dwg = svgwrite.Drawing(file_out, profile='basic')

    if tile_type.lower() in ['square', 'squares']:
        draw_func = dwg.rect
    elif tile_type.lower() in ['circle', 'circles']:
        draw_func = dwg.ellipse
    else:
        raise NotImplementedError

    for k, tile in enumerate(tiles.reshape(n_tiles_horizontal * n_tiles_vertical, 4), 1):
        print("{} / {} tiles".format(k, n_tiles_horizontal * n_tiles_vertical))
        # Draw i-est shadow tile
        dwg.add(draw_func(tile[:2], tile[2:], fill='#000000'))
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
                        help='Number of tiles to use horizontally. ' +
                             '(At least one of n-tiles-h and n-tiles-h must be provided)')
    parser.add_argument('--n-tiles-v', type=int, default=None,
                        help='Number of tiles to use vertically. ' +
                             '(At least one of n-tiles-h and n-tiles-h must be provided)')
    parser.add_argument('--tile-type', type=str, default='circles',
                        help="'squares' or 'circles'. (default : 'circles')")
    parser.add_argument('--min-thick', type=float, default=0.1,
                        help='Minimum thickness of the bright grid, in ratio of a tile size. (default : 0.1)')
    parser.add_argument('--min-tile-size', type=float, default=0.,
                        help='Minimum size of the tiles, in ratio of a tile size. (default : 0.)')
    parser.add_argument('--border', type=float, default=1.,
                        help='Border size around the generated svg, in ratio of a tile size. (default : 1.)')
    args = parser.parse_args()

    if args.file_out is None:
        args.file_out = os.path.splitext(args.file_in)[0] + '_tiles.svg'
    elif os.path.splitext(args.file_out)[-1] != '.svg':
        args.file_out += '.svg'

    to_tiles(file_in=args.file_in, file_out=args.file_out, invert=args.invert,
             n_tiles_horizontal=args.n_tiles_h, n_tiles_vertical=args.n_tiles_v, tile_type=args.tile_type,
             min_thick=args.min_thick, min_tile_size=args.min_tile_size, border=args.border)
