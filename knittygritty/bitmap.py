from PIL import Image
from os import path

from kh940 import Pattern

COLOR_MAP = {
    False: 0xffffff,
    True: 0x000000,
}

INV_COLOR_MAP = {
    (255, 255, 255): False,
    (0, 0, 0): True,
}


def write_pattern(pattern, filename):
    image = Image.new('RGB', (pattern.width, pattern.height))

    for y, row in enumerate(pattern.rows):
        for x, v in enumerate(row):
            image.putpixel((x, y), COLOR_MAP[v])

    image.save(filename)


def read_pattern(filename):
    image = Image.open(filename)
    width, height = image.size

    basename = path.basename(filename)
    dot_pos = basename.index('.')
    pattern_number = int(basename[:dot_pos])

    rows = []
    for y in range(height):
        row = []

        for x in range(width):
            v = INV_COLOR_MAP[image.getpixel((x, y))]

            row.append(v)

        rows.append(row)

    return Pattern(pattern_number, rows)
