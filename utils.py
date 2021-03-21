from numpy import ndarray


def contrast(image, invert=False):
    """
    Affine mapping from [min, max] to [0, 255] for uint8 arrays.

    Parameters
    ----------
    image : ndarray
        Input array [uint8].
    invert : bool, optional
        Invert bright and dark values. (default : False)

    Returns
    -------
    contrasted_image : ndarray
        Contrasted array with min=0, max=255 [uint8].
    """
    image = image.astype('float')
    if invert:
        image *= -1
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
