import argparse
import os

import cv2
import numpy as np
import svgwrite
from numpy import ndarray


def contrast(image):
    """
    Affine mapping from [min, max] to [0, 255] for uint8 arrays.

    Parameters
    ----------
    image : ndarray
        Input array [uint8].

    Returns
    -------
    contrasted_image : ndarray
        Contrasted array with min=0, max=255 [uint8].
    """
    image = image.astype('float')
    image -= image.min()
    image *= 255. / image.max()
    return image.round().astype('uint8')


def map_values(x, in_min, in_max, out_min, out_max):
    """
    Affine mapping from [in_min, in_max] to [out_min, out_max].

    Parameters
    ----------
    x : ndarray
        Input array.
    in_min : float
        Input range min ; will become out_min in output.
    in_max : float
        Input range max ; will become out_max in output.
    out_min : float
        Output range min ; was in_min in input.
    out_max : float
        Output range max ; was in_max in input.

    Returns
    -------
    mapped_array : ndarray
        Re-mapped array.
    """
    slope = (out_max - out_min) / (in_max - in_min)
    offset = out_max - slope * in_max
    return slope * x + offset


def vasarely_bands(file_in, file_out, n_bands=32, axis=1, min_thick=3., min_space=3., border=10.):
    """

    Parameters
    ----------
    file_in : str
        Path of the input image.
    file_out : str
        Path of the output SVG image.
    n_bands : int, optional
        Number of shadow bands to use. (default : 32)
    axis : int, optional
        1 for vertical bands, 0 for horizontal bands (default : 1).
    min_thick : float, optional
        Minimum thickness of a bright band (default : 3.).
    min_space : float, optional
        Minimum space between bright bands (default : 3.).
    border : float, optional
        Border around the results (default : 10.).
    """

    # Input as grayscale, and map to [0, 255].
    image = contrast(cv2.imread(file_in, 0))

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

    # Transpose for horizontal bands
    if axis == 0:
        shapes = np.flip(shapes, axis=-1)

    dwg = svgwrite.Drawing(file_out, profile='basic')
    for i, shape in enumerate(shapes, 1):
        print("{} / {} bands".format(i, n_bands))
        # Draw i-est shadow shape
        dwg.add(dwg.polygon(points=shape, fill='#000000'))
    # Draw border frame
    dwg.add(dwg.rect((0., 0.), (width_in + 2. * border, height_in + 2. * border), stroke='#000000', fill='none'))
    dwg.save(pretty=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file-in', type=str, required=True,
                        help='Path of the input image.')
    parser.add_argument('--file-out', type=str, default=None,
                        help='Path of the output SVG image. (default : input file but it\'s SVG)')
    parser.add_argument('--n-bands', type=int, default=32,
                        help='Number of shadow bands to use. (default : 32)')
    parser.add_argument('--axis', type=int, default=1,
                        help='1 for vertical bands, 0 for horizontal bands (default : 1).')
    parser.add_argument('--min-thick', type=float, default=3.,
                        help='Minimum thickness of a bright band, in px (default : 3.).')
    parser.add_argument('--min-space', type=float, default=3.,
                        help='Minimum space between bright bands, in px (default : 3.).')
    parser.add_argument('--border', type=float, default=10.,
                        help='Border size order around the results, in px (default : 10.).')
    args = parser.parse_args()

    if args.file_out is None:
        args.file_out = os.path.splitext(args.file_in)[0] + '.svg'
    elif os.path.splitext(args.file_out)[-1] != '.svg':
        args.file_out += '.svg'

    vasarely_bands(file_in=args.file_in, file_out=args.file_out, n_bands=args.n_bands, axis=args.axis,
                   min_thick=args.min_thick, min_space=args.min_space, border=args.border)
