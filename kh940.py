from collections import namedtuple

import math
import struct

import util

PATTERN_COUNT = 98

ControlData = namedtuple('ControlData', [
    'next_pattern_ptr1',       # 2
    'unknown1',                # 2
    'next_pattern_ptr2',       # 2
    'last_pattern_end_ptr',    # 2
    'unknown2',                # 2
    'last_pattern_start_ptr',  # 2
    'unknown3',                # 4
    'header_end_ptr',          # 2
    'unknown_ptr',             # 2
    'unknown4_1',              # 2
    'unknown4_2',              # 1
])

ControlData.struct = struct.Struct('>HHHHHHIHHHB')


def _make_empty_control_data():
    return ControlData(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)


def _memo_size(height):
    return int(math.ceil(height / 2.0))


def _pattern_data_sizes(width, height):
    row_nibbles = int(math.ceil(width / 4.0))
    row_pad_bits = util.padding(width, 4)

    initial_padding = util.padding(row_nibbles * height, 2)

    return row_nibbles, row_pad_bits, initial_padding


def _parse_pattern_rows(width, height, data):
    row_nibbles, row_pad_bits, initial_padding = _pattern_data_sizes(width, height)

    nibble_data = list(util.to_nibbles(data))

    rows = []

    for row in range(height):
        start_index = initial_padding + row_nibbles * row
        end_index = start_index + row_nibbles

        bits = list(util.nibble_bits(nibble_data[start_index:end_index]))

        rows.append([bool(b) for b in reversed(bits[row_pad_bits:])])

    return rows


def _read_pattern(data, header_idx):
    header = data[header_idx * 7:(header_idx + 1) * 7]

    end_offset = struct.unpack('>H', header[0:2])[0]
    data_nibbles = list(util.to_nibbles(header[2:]))
    height, width, ptn_num = map(util.from_bcd,
                                 [data_nibbles[0:3], data_nibbles[3:6], data_nibbles[7:10]])

    if not end_offset:
        return None

    memo_size = _memo_size(height)
    memo_end_pos = 0x7fff - end_offset
    memo_start_pos = memo_end_pos - memo_size

    memo = data[memo_start_pos + 1:memo_end_pos + 1]

    pattern_size = int(math.ceil(math.ceil(width / 4.0) * height / 2.0))
    pattern_end_pos = memo_start_pos
    pattern_start_pos = pattern_end_pos - pattern_size

    pattern = data[pattern_start_pos + 1:pattern_end_pos + 1]

    parsed = _parse_pattern_rows(width, height, pattern)

    return Pattern(ptn_num, parsed, memo)


def _read_data0(data):
    return data[0x7ee0:0x7f00]


def _read_control_data(data):
    control_data_str = data[0x7f00:0x7f17]
    return ControlData(*ControlData.struct.unpack(control_data_str))


def _read_data1(data):
    return data[0x7f17:0x7fea]


def _read_loaded_pattern(data):
    num_digits = list(util.to_nibbles(data[0x7fea:0x7fec]))

    return util.from_bcd(num_digits[1:])


def _read_data2(data):
    return data[0x7fec:0x8000]


class Pattern(object):
    def __init__(self, pattern_number, rows, memo=None):
        self.pattern_number = pattern_number
        self.rows = rows
        self.height = len(rows)

        assert self.height > 0

        self.width = len(rows[0])
        assert all(len(row) == self.width for row in rows)

        self.memo = memo or ('\x00' * _memo_size(self.height))

        assert len(self.memo) == _memo_size(self.height)

    def __repr__(self):
        return '<Pattern #%s (%sx%s)>' % (self.pattern_number, self.width, self.height)

    def _serialize_rows(self):
        row_nibbles, row_pad_bits, initial_padding = _pattern_data_sizes(self.width, self.height)

        bits = [0] * (initial_padding * 4)

        for row in self.rows:
            bits += [0] * row_pad_bits
            bits += [int(b) for b in reversed(row)]

        return util.bits_to_bytes(bits)

    def serialize_header(self, offset):
        offset_bytes = struct.pack('>H', offset)
        header_nibbles = sum([util.to_bcd(self.height, 3),
                              util.to_bcd(self.width, 3),
                              util.to_bcd(self.pattern_number, 4)],
                             [])

        return offset_bytes + util.from_nibbles(header_nibbles)

    def serialize_data(self):
        return self._serialize_rows() + self.memo


class MachineState(object):
    SERIALIZED_PATTERN_LIST_LENGTH = 686

    @classmethod
    def make_empty(cls):
        return cls(patterns=[],
                   data0='\x00' * 32,
                   control_data=_make_empty_control_data(),
                   data1='\x00' * 211,
                   loaded_pattern=0,
                   data2='\x00' * 20)

    @classmethod
    def with_patterns(cls, patterns):
        machine = cls.make_empty()
        machine.patterns = patterns
        machine.loaded_pattern = patterns[0].pattern_number if patterns else 0
        return machine

    def __init__(self, patterns,
                 data0,
                 control_data,
                 data1,
                 loaded_pattern,
                 data2):
        self.patterns = patterns
        self.data0 = data0
        self.control_data = control_data
        self.data1 = data1
        self.loaded_pattern = loaded_pattern
        self.data2 = data2

        assert len(data0) == 32
        assert len(data1) == 211
        assert len(data2) == 20

    def _serialize_control_data(self, pattern_layout):
        if pattern_layout:
            last_pattern, last_pattern_end = pattern_layout[-1]
            last_pattern_start = last_pattern_end + len(last_pattern.serialize_data())
            next_pattern_ptr = last_pattern_start + 1
        else:
            next_pattern_ptr = 0x120
            last_pattern_start = last_pattern_end = 0

        pattern_header_end = 0x8000 - (7 * len(pattern_layout)) - 7

        control_data = ControlData(next_pattern_ptr1=next_pattern_ptr,
                                   unknown1=self.control_data.unknown1,
                                   next_pattern_ptr2=next_pattern_ptr if pattern_layout else 0,
                                   last_pattern_end_ptr=last_pattern_end,
                                   unknown2=self.control_data.unknown2,
                                   last_pattern_start_ptr=last_pattern_start,
                                   unknown3=self.control_data.unknown3,
                                   header_end_ptr=pattern_header_end,
                                   unknown_ptr=self.control_data.unknown_ptr,
                                   unknown4_1=self.control_data.unknown4_1,
                                   unknown4_2=self.control_data.unknown4_2)

        return ControlData.struct.pack(*control_data)

    def _serialize_loaded_pattern(self):
        return util.from_nibbles([1] + util.to_bcd(self.loaded_pattern, width=3))

    def _layout_pattern_memory(self):
        offset = 0x120
        layout = []

        for pattern in self.patterns:
            layout.append((pattern, offset))
            offset += len(pattern.serialize_data())

        return layout

    def _serialize_pattern_list(self, pattern_layout):
        data = ''

        for pattern, offset in pattern_layout:
            data += pattern.serialize_header(offset)

        if len(pattern_layout) < PATTERN_COUNT and pattern_layout:
            max_number = max(p.pattern_number for p in self.patterns)
        else:
            max_number = 900

        data += '\x00\x00\x00\x00\x00' + util.from_nibbles(util.to_bcd(max_number + 1, 4))

        pad_patterns = 97 - len(pattern_layout)
        data += '\x00' * (pad_patterns * 7)

        assert len(data) == self.SERIALIZED_PATTERN_LIST_LENGTH

        return data

    def _serialize_pattern_memory_padding(self, pattern_layout):
        if pattern_layout:
            last_pattern, last_offset = pattern_layout[-1]
            last_pattern_end = last_offset + len(last_pattern.serialize_data())
        else:
            last_pattern_end = 0x120

        pattern_pad = 0x8000 - last_pattern_end - self.SERIALIZED_PATTERN_LIST_LENGTH

        return '\x00' * pattern_pad

    def _serialize_pattern_memory(self, pattern_layout):
        data = ''

        for pattern, offset in reversed(pattern_layout):
            data += pattern.serialize_data()

        return data

    def serialize(self):
        pattern_layout = self._layout_pattern_memory()

        data = ''
        data += self._serialize_pattern_list(pattern_layout)
        data += self._serialize_pattern_memory_padding(pattern_layout)
        data += self._serialize_pattern_memory(pattern_layout)
        data += self.data0
        data += self._serialize_control_data(pattern_layout)
        data += self.data1
        data += self._serialize_loaded_pattern()
        data += self.data2

        assert len(data) == 32768

        return data

    def pattern_with_number(self, pattern_number):
        for pattern in self.patterns:
            if pattern.pattern_number == pattern_number:
                return pattern

        return None


def parse_memory_dump(data):
    patterns = filter(bool, [_read_pattern(data, i) for i in range(PATTERN_COUNT)])
    data0 = _read_data0(data)
    control_data = _read_control_data(data)
    data1 = _read_data1(data)
    loaded_pattern = _read_loaded_pattern(data)
    data2 = _read_data2(data)

    state = MachineState(patterns,
                         data0,
                         control_data,
                         data1,
                         loaded_pattern,
                         data2)

    return state
