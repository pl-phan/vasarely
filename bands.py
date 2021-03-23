import argparse
import os

import cv2
import numpy as np
import svgwrite

from utils import contrast, map_values


def to_bands(file_in, file_out, invert=False,
             n_bands=32, axis=1, resolution=320,
             min_thick=0.1, min_space=0.1, border=1.):
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
    resolution : int, optional
        Resolution of each band. (default : 320)
    min_thick : float, optional
        Minimum thickness of a bright band, in ratio of a band width. (default : 0.1)
    min_space : float, optional
        Minimum space between adjacent bright bands, in ratio of a band width. (default : 0.1)
    border : float, optional
        Border size around the generated svg, in ratio of a band width. Choose 0 for no border. (default : 1.)
    """

    # Input as grayscale, and map to [0, 255].
    image = contrast(cv2.imread(file_in, 0), invert=invert)
    if axis == 0:
        # Transpose for horizontal bands.
        image = image.T
    height_in, width_in = image.shape
    band_width = width_in / n_bands

    # Resize width to nearest multiple, for equally sized bands.
    width_out = round(band_width) * n_bands
    image = cv2.resize(image, (width_out, resolution), interpolation=cv2.INTER_LINEAR)

    # Compute shadow bands widths, with means over pixel groups.
    values = image.reshape(resolution, n_bands, width_out // n_bands).mean(axis=-1)

    # Array to be filled with the coordinates [X, Y] for the 'resolution * 2' points of each shadow shape contour.
    # value == 0. means largest shadow band, value == 255. means thinnest shadow band.
    shapes = np.empty((n_bands, 2, resolution, 2), dtype='float')
    # Point coordinates on parallel lines.
    shapes[:, :, :, 0] = 0.5 + np.arange(n_bands)[:, np.newaxis, np.newaxis]
    shapes[:, :, :, 1] = np.arange(resolution) / resolution
    # Deform shapes according to image values.
    sizes = map_values(values, 0., 255., 1. - min_thick, min_space).T
    shapes[:, 0, :, 0] -= sizes / 2.
    shapes[:, 1, :, 0] += sizes / 2.
    # Flip last half of values upside down, to outline the shape with ordered points.
    shapes[:, 1] = np.flip(shapes[:, 1], axis=1)

    # Merge to an array of shapes
    shapes = shapes.reshape(n_bands, 2 * resolution, 2)

    # Upscale to original dimensions
    shapes *= band_width, height_in

    # Frame
    border *= band_width
    shapes += border
    frame = np.zeros((4, 2), dtype='float')
    frame[2:4, 0] = width_in + 2. * border
    frame[1:3, 1] = height_in + 2. * border

    if axis == 0:
        # Transpose for horizontal bands
        shapes = np.flip(shapes, axis=-1)
        frame = np.flip(frame, axis=-1)

    dwg = svgwrite.Drawing(file_out, profile='basic')
    # Draw
    for shape in shapes:
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
    parser.add_argument('--resolution', type=int, default=320,
                        help='Resolution of each band. (default : 320)')
    parser.add_argument('--min-thick', type=float, default=0.1,
                        help='Minimum thickness of a bright band, in ratio of a band width. (default : 0.1)')
    parser.add_argument('--min-space', type=float, default=0.1,
                        help='Minimum space between adjacent bright bands, in ratio of a band width. (default : 0.1)')
    parser.add_argument('--border', type=float, default=1.,
                        help='Border size around the generated svg, in ratio of a band width. ' +
                             'Choose 0 for no border. (default : 1.)')
    args = parser.parse_args()

    if args.file_out is None:
        args.file_out = os.path.splitext(args.file_in)[0] + '_bands.svg'
    elif os.path.splitext(args.file_out)[-1] != '.svg':
        args.file_out += '.svg'

    to_bands(file_in=args.file_in, file_out=args.file_out, invert=args.invert,
             n_bands=args.n_bands, axis=args.axis, resolution=args.resolution,
             min_thick=args.min_thick, min_space=args.min_space, border=args.border)
