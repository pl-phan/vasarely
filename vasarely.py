import argparse

import cv2
import numpy as np


def bands(image, n, axis=1, min_space=4, min_band=4):
    shape_in = image.shape

    half_band = round(shape_in[axis] / (2 * n))
    half_min_space = min_space // 2 + (min_space % 2 != 0) - 1
    half_min_band = min_band // 2 + (min_band % 2 != 0) - 1

    if shape_in[axis] == 2 * half_band * n:
        shape_out = shape_in
    else:
        shape_out = [None, None]
        shape_out[axis] = 2 * half_band * n
        shape_out[1 - axis] = round(shape_in[1 - axis] * shape_out[axis] / shape_in[axis])
        shape_out = tuple(shape_out)
        image = cv2.resize(image, (shape_out[1], shape_out[0]), interpolation=cv2.INTER_LINEAR)

    pattern = np.concatenate((
        np.array([1. for _ in range(half_min_space)]),
        np.linspace(1., 0., num=half_band - (half_min_band + half_min_space)),
        np.array([0. for _ in range(2 * half_min_band)]),
        np.linspace(0., 1., num=half_band - (half_min_band + half_min_space)),
        np.array([1. for _ in range(half_min_space)])
    ))
    if axis == 1:
        pattern = np.tile(pattern, (shape_out[0], n))
        values = image.reshape(shape_out[0] * n, shape_out[1] // n, order='C').mean(axis=1)
        values = values.reshape(shape_out[0], n, order='C').repeat(half_band * 2, axis=1) / 255.
    else:
        pattern = pattern[:, np.newaxis]
        pattern = np.tile(pattern, (n, shape_out[1]))
        values = image.reshape(shape_out[0] // n, shape_out[1] * n, order='F').mean(axis=0)
        values = values.reshape(n, shape_out[1], order='F').repeat(half_band * 2, axis=0) / 255.

    out = ((values > pattern) * 255.).astype('uint8')

    if shape_out[0] != shape_in[0]:
        out = cv2.resize(out, (shape_in[1], shape_in[0]), interpolation=cv2.INTER_LINEAR)

    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file-in', type=str, required=True, help='Input image path')
    parser.add_argument('--file-out', type=str, required=True, help='Output image path')
    parser.add_argument('--axis', type=int, default=1, help='0 or 1 (default: 1, yields vertical bands)')
    args = parser.parse_args()

    image_in = cv2.imread(args.file_in, 0)
    image_out = bands(image_in, 60, axis=args.axis)
    cv2.imwrite(args.file_out, image_out)
