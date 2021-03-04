import cv2
import numpy as np


def vertical(image, n, min_space=2, min_width=2):
    height, width = image.shape

    half_band = round(width / (2 * n))
    half_min_space = min_space // 2 + (min_space % 2 > 0) - 1
    half_min_width = min_width // 2 + (min_width % 2 > 0) - 1

    if width != 2 * half_band * n:
        height = round(height * (2 * half_band * n) / width)
        width = 2 * half_band * n
        image = cv2.resize(image, (width, height), interpolation=cv2.INTER_LINEAR)

    pattern = np.concatenate((
        np.array([1. for _ in range(half_min_space)]),
        np.linspace(1., 0., num=half_band - (half_min_width + half_min_space)),
        np.array([0. for _ in range(2 * half_min_width)]),
        np.linspace(0., 1., num=half_band - (half_min_width + half_min_space)),
        np.array([1. for _ in range(half_min_space)])
    ))
    pattern = np.tile(pattern, (height, n))
    values = image.reshape(height * n, width // n).mean(axis=1)
    values = values.reshape(height, n).repeat(half_band * 2, axis=1) / 255.

    out = (values > pattern) * 255.

    return out.astype('uint8')


def horizontal(image, n, min_space=2, min_height=2):
    height, width = image.shape

    half_band = round(height / (2 * n))
    half_min_space = min_space // 2 + (min_space % 2 > 0) - 1
    half_min_height = min_height // 2 + (min_height % 2 > 0) - 1

    if height != 2 * half_band * n:
        width = round(width * (2 * half_band * n) / height)
        height = 2 * half_band * n
        image = cv2.resize(image, (width, height), interpolation=cv2.INTER_LINEAR)

    pattern = np.concatenate((
        np.array([1. for _ in range(half_min_space)]),
        np.linspace(1., 0., num=half_band - (half_min_height + half_min_space)),
        np.array([0. for _ in range(2 * half_min_height)]),
        np.linspace(0., 1., num=half_band - (half_min_height + half_min_space)),
        np.array([1. for _ in range(half_min_space)])
    )).reshape(-1, 1)
    pattern = np.tile(pattern, (n, width))
    values = image.reshape(height // n, width * n, order='F').mean(axis=0)
    values = values.reshape(n, width, order='F').repeat(half_band * 2, axis=0) / 255.

    out = (values > pattern) * 255.

    return out.astype('uint8')


if __name__ == '__main__':
    file_in = './haiti.png'
    file_out = './haiti_out_v.png'

    image_in = cv2.imread(file_in, 0)
    image_out = vertical(image_in, 50)
    # image_out = horizontal(image_in, 50)
    cv2.imwrite(file_out, image_out)
