import argparse
import os

import cv2
import numpy as np
import svgwrite

from utils import contrast, map_values


def to_bands(file_in, file_out, invert=False, n_bands=32, axis=1, min_thick=0.1, min_space=0.1, border=1.):
    """
    Reproduce an image with parallel bands.

    Parameters
    ----------
    file_in : str
        Path of the input image.
    file_out : str
        Path of the output SVG image.
    invert : bool, optional
        Invert bright and dark values. (default : False)
    n_bands : int, optional
        Number of shadow bands to use. (default : 32)
    axis : int, optional
        1 for vertical bands, 0 for horizontal bands. (default : 1)
    min_thick : float, optional
        Minimum thickness of a bright band, in ratio of a band width. (default : 0.1)
    min_space : float, optional
        Minimum space between adjacent bright bands, in ratio of a band width. (default : 0.1)
    border : float, optional
        Border size around the generated svg, in ratio of a tile size. Choose 0 for no border. (default : 1.)
    """

    # Input as grayscale, and map to [0, 255].
    image = contrast(cv2.imread(file_in, 0), invert=invert)

    # Transpose for horizontal bands.
    if axis == 0:
        image = image.T

    height_in, width_in = image.shape

    # Resize to nearest multiple, for equal sized bands.
    band_width = round(width_in / n_bands)
    width_out = band_width * n_bands
    height_out = round(height_in * width_out / width_in)
    image = cv2.resize(image, (width_out, height_out), interpolation=cv2.INTER_LINEAR)
    scale_factor = width_out / width_in

    # Convert in band_with unit to px.
    min_thick *= band_width
    min_space *= band_width
    border *= band_width

    # Compute shadow bands widths, with means over pixel groups.
    values = image.reshape(height_out, n_bands, width_out // n_bands).mean(axis=2)

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
    parser.add_argument('--n-bands', type=int, default=32,
                        help='Number of shadow bands to use. (default : 32)')
    parser.add_argument('--axis', type=int, default=1,
                        help='1 for vertical bands, 0 for horizontal bands. (default : 1)')
    parser.add_argument('--min-thick', type=float, default=0.1,
                        help='Minimum thickness of a bright band, in ratio of a band width. (default : 0.1)')
    parser.add_argument('--min-space', type=float, default=0.1,
                        help='Minimum space between adjacent bright bands, in ratio of a band width. (default : 0.1)')
    parser.add_argument('--border', type=float, default=1.,
                        help='Border size around the generated svg, in ratio of a tile size. ' +
                             'Choose 0 for no border. (default : 1.)')
    args = parser.parse_args()

    if args.file_out is None:
        args.file_out = os.path.splitext(args.file_in)[0] + '_bands.svg'
    elif os.path.splitext(args.file_out)[-1] != '.svg':
        args.file_out += '.svg'

    to_bands(file_in=args.file_in, file_out=args.file_out, invert=args.invert,
             n_bands=args.n_bands, axis=args.axis,
             min_thick=args.min_thick, min_space=args.min_space, border=args.border)
