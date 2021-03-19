import argparse
import os

import cv2
import numpy as np
import svgwrite

from utils import contrast, map_values


def bands(file_in, file_out, n_squares=32, min_thick=3., min_square_size=3., border=10.):
    """
    Reproduce an image with dark parallel bands.

    Parameters
    ----------
    file_in : str
        Path of the input image.
    file_out : str
        Path of the output SVG image.
    n_squares : int, optional
        Number of horizontal squares to use. (default : 32)
    min_thick : float, optional
        Minimum thickness of the bright grid, in px. (default : 3.)
    min_square_size : float, optional
        Minimum size of the squares, in px. (default : 3.)
    border : float, optional
        Border size around the result, in px. (default : 10.)
    """

    # Input as grayscale, and map to [0, 255].
    image = contrast(cv2.imread(file_in, 0))

    height_in, width_in = image.shape

    # Resize to nearest multiple, for equal sized squares.
    square_size = round(width_in / n_squares)
    width_out = square_size * n_squares

    height_out = round(height_in * width_out / width_in)
    image = cv2.resize(image, (width_out, height_out), interpolation=cv2.INTER_LINEAR)
    scale_factor = width_out / width_in

    # Compute shadow bands widths, with means over pixel groups.
    values = image.reshape(height_out * n_bands, width_out // n_bands).mean(axis=1)
    values = values.reshape(height_out, n_bands)

    shapes = np.empty((n_bands, 2 * height_out, 2), dtype='float')
    # Array will be filled with the coordinates for the
    # 'height_out * 2' points of each shadow shape contour.

    heights = np.arange(height_out) / scale_factor
    for k in range(n_bands):
        # value == 0. means largest shadow band,
        # value == 255. means thinnest shadow band.

        # Points on the left, going down.
        shapes[k, :height_out, 0] = map_values(
            values[:, k], 0., 255.,
            k * band_width / scale_factor + min_thick / 2.,
            (k + 0.5) * band_width / scale_factor - min_space / 2.,
        )
        shapes[k, :height_out, 1] = heights

        # Points on the right, going up.
        shapes[k, height_out:, 0] = np.flipud(map_values(
            values[:, k], 255., 0.,
            (k + 0.5) * band_width / scale_factor + min_space / 2.,
            (k + 1) * band_width / scale_factor - min_thick / 2.,
        ))
        shapes[k, height_out:, 1] = np.flipud(heights)

    # Offset both x and y, so the whole array
    shapes += border

    # Frames corners
    frame = np.zeros((4, 2), dtype='float')
    frame[1:3, 1] = height_in + 2. * border
    frame[2:4, 0] = width_in + 2. * border

    # Transpose for horizontal bands
    if axis == 0:
        shapes = np.flip(shapes, axis=-1)
        frame = np.flip(frame, axis=-1)

    dwg = svgwrite.Drawing(file_out, profile='basic')
    for i, shape in enumerate(shapes, 1):
        print("{} / {} bands".format(i, n_bands))
        # Draw i-est shadow shape
        dwg.add(dwg.polygon(points=shape, fill='#000000'))
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
    parser.add_argument('--n-squares', type=int, default=32,
                        help='Number of horizontal squares to use. (default : 32)')
    parser.add_argument('--min-thick', type=float, default=3.,
                        help='Minimum thickness of the bright grid, in px. (default : 3.)')
    parser.add_argument('--min-square-size', type=float, default=3.,
                        help='Minimum size of the squares, in px. (default : 3.)')
    parser.add_argument('--border', type=float, default=10.,
                        help='Border size around the result, in px. (default : 10.)')
    args = parser.parse_args()

    if args.file_out is None:
        args.file_out = os.path.splitext(args.file_in)[0] + '.svg'
    elif os.path.splitext(args.file_out)[-1] != '.svg':
        args.file_out += '.svg'

    bands(file_in=args.file_in, file_out=args.file_out, n_squares=args.n_squares,
          min_thick=args.min_thick, min_square_size=args.min_square_size, border=args.border)
