import argparse
import os

import cv2
import numpy as np
import svgwrite

from utils import contrast, map_values


def to_squares(file_in, file_out, n_squares_horizontal=None, n_squares_vertical=None,
               min_thick=1., min_square_size=0., border=10.):
    """
    Reproduce an image with dark mosaic.

    Parameters
    ----------
    file_in : str
        Path of the input image.
    file_out : str
        Path of the output SVG image.
    n_squares_horizontal : int, optional
        Number of squares to use horizontally.
    n_squares_vertical : int, optional
        Number of squares to use vertically.
    min_thick : float, optional
        Minimum thickness of the bright grid, in px. (default : 1.)
    min_square_size : float, optional
        Minimum size of the squares, in px. (default : 0.)
    border : float, optional
        Border size around the result, in px. (default : 10.)
    """

    # Input as grayscale, and map to [0, 255].
    image = contrast(cv2.imread(file_in, 0))
    height_in, width_in = image.shape

    if n_squares_horizontal is None and n_squares_vertical is None:
        raise AssertionError('Either n_squares_horizontal or n_squares_vertical must be specified.')
    if n_squares_vertical is None:
        n_squares_vertical = round(n_squares_horizontal * height_in / width_in)
    if n_squares_horizontal is None:
        n_squares_horizontal = round(n_squares_vertical * width_in / height_in)

    # Resize to nearest multiple, for equally sized squares.
    square_width = round(width_in / n_squares_horizontal)
    width_out = square_width * n_squares_horizontal
    square_height = round(height_in / n_squares_vertical)
    height_out = square_height * n_squares_vertical

    image = cv2.resize(image, (width_out, height_out), interpolation=cv2.INTER_LINEAR)
    scale_factor_horizontal = width_out / width_in
    scale_factor_vertical = height_out / height_in

    # Compute square sizes, with mean over each area.
    values = image.reshape(
        n_squares_vertical, height_out // n_squares_vertical,
        n_squares_horizontal, width_out // n_squares_horizontal
    ).mean(axis=(1, 3))

    squares = np.empty((n_squares_vertical, n_squares_horizontal, 4), dtype='float')
    # Array will be filled with the coordinates for the (X, Y, W, H) elements of each square.

    squares[:, :, 0] = ((np.arange(n_squares_horizontal) + 0.5) * square_width / scale_factor_horizontal)[np.newaxis, :]
    squares[:, :, 1] = ((np.arange(n_squares_vertical) + 0.5) * square_height / scale_factor_vertical)[:, np.newaxis]

    squares[:, :, 2] = map_values(values, 0., 255., square_width / scale_factor_horizontal - min_thick, min_square_size)
    squares[:, :, 3] = map_values(values, 0., 255., square_height / scale_factor_vertical - min_thick, min_square_size)

    squares[:, :, 0] -= squares[:, :, 2] / 2.
    squares[:, :, 1] -= squares[:, :, 3] / 2.

    # Offset both x and y
    squares[:, :, :2] += border

    # Frames corners
    frame = np.zeros((4, 2), dtype='float')
    frame[1:3, 1] = height_in + 2. * border
    frame[2:4, 0] = width_in + 2. * border

    dwg = svgwrite.Drawing(file_out, profile='basic')
    for k, square in enumerate(squares.reshape(n_squares_horizontal * n_squares_vertical, 4), 1):
        print("{} / {} squares".format(k, n_squares_horizontal * n_squares_vertical))
        # Draw i-est shadow shape
        dwg.add(dwg.rect(insert=square[:2], size=square[2:], fill='#000000'))
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
    parser.add_argument('--n-squares-h', type=int, default=None,
                        help='Number of squares to use horizontally. ' +
                             '(At least one of n-squares-h and n-squares-h must be provided)')
    parser.add_argument('--n-squares-v', type=int, default=None,
                        help='Number of squares to use vertically. ' +
                             '(At least one of n-squares-h and n-squares-h must be provided)')
    parser.add_argument('--min-thick', type=float, default=1.,
                        help='Minimum thickness of the bright grid, in px. (default : 1.)')
    parser.add_argument('--min-square-size', type=float, default=0.,
                        help='Minimum size of the squares, in px. (default : 0.)')
    parser.add_argument('--border', type=float, default=10.,
                        help='Border size around the result, in px. (default : 10.)')
    args = parser.parse_args()

    if args.file_out is None:
        args.file_out = os.path.splitext(args.file_in)[0] + '.svg'
    elif os.path.splitext(args.file_out)[-1] != '.svg':
        args.file_out += '.svg'

    to_squares(file_in=args.file_in, file_out=args.file_out,
               n_squares_horizontal=args.n_squares_h, n_squares_vertical=args.n_squares_v,
               min_thick=args.min_thick, min_square_size=args.min_square_size, border=args.border)
