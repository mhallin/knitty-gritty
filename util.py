def nibble_bits(ns):
    '''Convert a stream of 4 bit numbers to a stream of bits

    >>> list(nibble_bits([1, 2]))
    [0, 0, 0, 1, 0, 0, 1, 0]
    '''

    for n in ns:
        yield (n & 0x8) >> 3
        yield (n & 0x4) >> 2
        yield (n & 0x2) >> 1
        yield (n & 0x1) >> 0


def to_nibbles(bs):
    '''Convert a string of bytes to a stream of nibbles

    >>> list(to_nibbles('\x3d'))
    [3, 13]
    '''

    for c in bs:
        b = ord(c)

        yield (b & 0xf0) >> 4
        yield b & 0x0f


def from_nibbles(ns):
    '''Convert a stream of nibbles to a string of bytes

    >>> from_nibbles([3, 13])
    '\x3d'
    '''
    s = ''

    for n1, n2 in zip(ns[::2], ns[1::2]):
        s += chr((n1 << 4) | n2)

    return s


def from_bcd(ns):
    '''Convert a stream of nibbles representing a BCD
    (binary coded digit) to an integer.

    >>> from_bcd([1, 2, 3])
    123
    '''
    s = 0
    m = 1

    for n in reversed(ns):
        s += n * m
        m *= 10

    return s


def to_bcd(n, width=0):
    '''Convert an integer to a list of nibbles representing
    the number in BCD, optionally padded with initial zeroes
    to a specific width.

    >>> to_bcd(123)
    [1, 2, 3]
    >>> to_bcd(12, width=5)
    [0, 0, 0, 1, 2]
    '''
    l = []

    while n:
        l.append(n % 10)
        n /= 10

    if len(l) < width:
        l += [0] * (width - len(l))

    return list(reversed(l))


def bits_to_bytes(bits):
    '''Convert a sequence of bits to a string of bytes. The bit
    sequence must have a length divisible by 8

    >>> bits_to_bytes([0, 0, 1, 0, 0, 1, 0, 1])
    '\x25'
    '''
    assert len(bits) % 8 == 0

    acc = ''
    for i in range(len(bits) / 8):
        s = 0
        c = 128
        for b in range(8):
            s += bits[i * 8 + b] * c
            c /= 2

        acc += chr(s)

    return acc


def padding(n, alignment):
    '''Return the required padding for aligning `n` at `alignment`

    >>> padding(3, 4)
    1
    >>> padding(4, 4)
    0
    '''
    return (alignment - (n % alignment)) % alignment
