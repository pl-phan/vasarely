import argparse
import os

import cv2
import numpy as np
import svgwrite

from utils import contrast, map_values


def bands(image, n_bands, axis=1, min_thick=1., min_space=1.):
    if axis == 0:
        shapes = bands(image.T, n_bands, axis=1, min_thick=min_thick, min_space=min_space)
        return np.flip(shapes, axis=-1)

    height_in, width_in = image.shape
    band_width = round(width_in / n_bands)

    width_out = band_width * n_bands
    height_out = round(height_in * width_out / width_in)
    upscale = width_out / width_in
    print(upscale)
    image = cv2.resize(image, (width_out, height_out), interpolation=cv2.INTER_LINEAR)

    values = image.reshape(height_out * n_bands, width_out // n_bands).mean(axis=1)
    values = values.reshape(height_out, n_bands) / 255.

    shapes = np.empty((n_bands, 2 * height_out, 2), dtype='float')
    ys = np.arange(height_out) / upscale
    for k in range(n_bands):
        shapes[k, :height_out, 0] = map_values(
            values[:, k], 0., 1.,
            k * band_width / upscale + min_space / 2.,
            (k + 0.5) * band_width / upscale - min_thick / 2.,
        )
        shapes[k, :height_out, 1] = ys

        shapes[k, height_out:, 0] = np.flipud(map_values(
            values[:, k], 1., 0.,
            (k + 0.5) * band_width / upscale + min_thick / 2.,
            (k + 1) * band_width / upscale - min_space / 2.,
        ))
        shapes[k, height_out:, 1] = np.flipud(ys)

    return shapes


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file-in', type=str, required=True, help='Input image')
    parser.add_argument('--file-out', type=str, required=True, help='Output image')
    parser.add_argument('--n-bands', type=int, default=32, help='Number of bands to use')
    parser.add_argument('--axis', type=int, default=1, help='0 or 1 (default: 1 for vertical bands)')
    parser.add_argument('--min-thick', type=float, default=1., help='Minimum thickness of a shape (in px)')
    parser.add_argument('--min-space', type=float, default=1., help='Minimum space between shapes (in px)')
    args = parser.parse_args()

    if os.path.splitext(args.file_out)[-1] != '.svg':
        args.file_out += '.svg'

    image_in = cv2.imread(args.file_in, 0)
    image_in = contrast(image_in)

    pts_shapes = bands(image_in, n_bands=args.n_bands, axis=args.axis,
                       min_thick=args.min_thick, min_space=args.min_space)

    dwg = svgwrite.Drawing(args.file_out, profile='basic')
    for i, pts in enumerate(pts_shapes):
        print("{} / {} bands".format(i, args.n_bands))
        dwg.add(dwg.polygon(points=pts, fill=svgwrite.rgb(10, 10, 10)))
    dwg.save(pretty=True)
