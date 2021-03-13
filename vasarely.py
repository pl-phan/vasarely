import argparse
import os

import cv2
import numpy as np
import svgwrite

from utils import contrast, map_values


def bands(file_in, file_out, n_bands=32, axis=1, min_thick=1., min_space=1., border=10.):
    image = contrast(cv2.imread(file_in, 0))

    if axis == 0:
        image = image.T

    height_in, width_in = image.shape
    band_width = round(width_in / n_bands)

    width_out = band_width * n_bands
    height_out = round(height_in * width_out / width_in)
    upscale = width_out / width_in
    image = cv2.resize(image, (width_out, height_out), interpolation=cv2.INTER_LINEAR)

    values = image.reshape(height_out * n_bands, width_out // n_bands).mean(axis=1)
    values = values.reshape(height_out, n_bands)

    shapes = np.empty((n_bands, 2 * height_out, 2), dtype='float')
    ys = np.arange(height_out) / upscale
    for k in range(n_bands):
        shapes[k, :height_out, 0] = map_values(
            values[:, k], 0., 255.,
            k * band_width / upscale + min_space / 2.,
            (k + 0.5) * band_width / upscale - min_thick / 2.,
        )
        shapes[k, :height_out, 1] = ys

        shapes[k, height_out:, 0] = np.flipud(map_values(
            values[:, k], 255., 0.,
            (k + 0.5) * band_width / upscale + min_thick / 2.,
            (k + 1) * band_width / upscale - min_space / 2.,
        ))
        shapes[k, height_out:, 1] = np.flipud(ys)
    shapes += border

    if axis == 0:
        shapes = np.flip(shapes, axis=-1)

    dwg = svgwrite.Drawing(file_out, profile='basic')
    for i, shape in enumerate(shapes, 1):
        print("{} / {} bands".format(i, n_bands))
        dwg.add(dwg.polygon(points=shape, fill='#000000'))
    dwg.add(dwg.rect((0., 0.), (width_in + 2. * border, height_in + 2. * border),
                     stroke='#000000', fill='none'))
    dwg.save(pretty=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file-in', type=str, required=True, help='Input image')
    parser.add_argument('--file-out', type=str, default=None, help='Output image')
    parser.add_argument('--n-bands', type=int, default=32, help='Number of bands to use')
    parser.add_argument('--axis', type=int, default=1, help='0 or 1 (default: 1 for vertical bands)')
    parser.add_argument('--min-thick', type=float, default=1., help='Minimum thickness of a shape (in px)')
    parser.add_argument('--min-space', type=float, default=1., help='Minimum space between shapes (in px)')
    parser.add_argument('--border', type=float, default=10., help='Size of the border (in px)')
    args = parser.parse_args()

    if args.file_out is None:
        args.file_out = os.path.splitext(args.file_in)[0] + '.svg'
    elif os.path.splitext(args.file_out)[-1] != '.svg':
        args.file_out += '.svg'

    bands(file_in=args.file_in, file_out=args.file_out, n_bands=args.n_bands, axis=args.axis,
          min_thick=args.min_thick, min_space=args.min_space, border=args.border)
