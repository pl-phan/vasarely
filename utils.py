import numpy as np


def contrast(image):
    image = image.astype('float')
    image -= image.min()
    image *= 255. / image.max()
    return image.round().astype('uint8')


def map_values(x, in_min, in_max, out_min, out_max):
    slope = (out_max - out_min) / (in_max - in_min)
    offset = out_max - slope * in_max
    return slope * x + offset
