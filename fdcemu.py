import base64
import json

from serial import Serial


class Sector(object):
    SECTOR_ID_LENGTH = 12
    DATA_LENGTH = 1024

    def __init__(self, sector_id=None, data=None):
        self.sector_id = sector_id or ('\x00' * self.SECTOR_ID_LENGTH)
        self.data = data or ('\x00' * self.DATA_LENGTH)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        assert len(value) == Sector.DATA_LENGTH
        self._data = value

    @property
    def sector_id(self):
        return self._sector_id

    @sector_id.setter
    def sector_id(self, value):
        assert len(value) == Sector.SECTOR_ID_LENGTH
        self._sector_id = value


class Disk(object):
    SECTOR_COUNT = 80

    def __init__(self, filename=None):
        if filename:
            with open(filename, 'r') as f:
                data = json.load(f)

            self.sectors = [
                Sector(base64.b64decode(sector['id'].encode('utf-8')),
                       base64.b64decode(sector['data'].encode('utf-8')))
                for sector in data['sectors']
            ]

        else:
            self.sectors = [Sector() for i in range(self.SECTOR_COUNT)]

        self.filename = filename

    def index_of_id(self, sector_id):
        for i, sector in enumerate(self.sectors):
            if sector.sector_id == sector_id:
                return i

        return -1

    def concat_sectors(self, count=SECTOR_COUNT):
        data = ''

        for sector in self.sectors[:count]:
            data += sector.data

        return data

    def set_concat_sector_data(self, data):
        i = 0

        while data[i * Sector.DATA_LENGTH:(i + 1) * Sector.DATA_LENGTH]:
            sector = self.sectors[i]
            sector.data = data[i * Sector.DATA_LENGTH:(i + 1) * Sector.DATA_LENGTH]
            sector.sector_id = '\x01' + '\x00' * (Sector.SECTOR_ID_LENGTH - 1)

            i += 1

    def save(self, filename=None):
        data = {
            'sectors': [{'id': base64.b64encode(sector.sector_id),
                         'data': base64.b64encode(sector.data)}
                        for sector in self.sectors]
        }

        if filename is None:
            filename = self.filename

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)


class FDCServer(object):
    MODE_OP = 'op'
    MODE_FDC = 'fdc'

    def __init__(self, port, disk):
        self.port = Serial(port=port,
                           baudrate=9600,
                           parity='N',
                           stopbits=1,
                           timeout=1,
                           xonxoff=0,
                           rtscts=0,
                           dsrdtr=0)
        self.disk = disk

        if not self.port:
            raise IOError('Could not open serial device %s' % port)

        self.port.setRTS(True)

        self.mode = self.MODE_OP

    def close(self):
        self.port.close()

    def run(self):
        while True:
            self.step()

    def step(self):
        if self.mode == self.MODE_OP:
            self.step_op()
        elif self.mode == self.MODE_FDC:
            self.step_fdc()
        else:
            raise Exception('Invalid mode %s' % self.mode)

    def step_op(self):
        zz = self.read(2, True)
        assert zz == 'ZZ'

        cmd = ord(self.read(1))
        datalen = ord(self.read(1))
        data = self.read(datalen)
        expected_chksum = ord(self.read(1))

        print 'op %s %s %s %s' % (cmd, datalen, data, expected_chksum)

        if cmd == 0x08:
            self.mode = self.MODE_FDC
        else:
            raise Exception('Unknown OP command %s' % cmd)

    def step_fdc(self):
        req_cmd, req_args = self.read_fdc_request()

        print 'got %s %s' % (req_cmd, req_args)

        if req_cmd == 'A':
            self.step_fdc_read_id_section(req_args)
        elif req_cmd == 'S':
            self.step_fdc_search_id_section(req_args)
        elif req_cmd in ('B', 'C'):
            self.step_fdc_write_id_section(req_args)
        elif req_cmd in ('W', 'X'):
            self.step_fdc_write_sector(req_args)
        elif req_cmd == 'R':
            self.step_fdc_read_sector(req_args)
        else:
            raise Exception('Unknown FDC emu command %s' % req_cmd)

    def step_fdc_read_id_section(self, req_args):
        assert len(req_args) == 1

        sector_index = int(req_args[0], 10)
        sector = self.disk.sectors[sector_index]

        response = '00%02X0000' % sector_index
        self.port.write(response)

        wait_value = self.read(1)
        assert wait_value == '\r'

        self.port.write(sector.sector_id)

    def step_fdc_search_id_section(self, req_args):
        assert len(req_args) == 0

        self.port.write('00000000')

        sector_id = self.read(Sector.SECTOR_ID_LENGTH)
        sector_index = self.disk.index_of_id(sector_id)

        if sector_index == -1:
            self.port.write('40000000')
        else:
            self.port.write('00%02X0000' % sector_index)

    def step_fdc_write_id_section(self, req_args):
        assert len(req_args) == 1

        sector_index = int(req_args[0], 10)
        sector = self.disk.sectors[sector_index]

        self.port.write('00%02X0000' % sector_index)

        sector_id = self.read(Sector.SECTOR_ID_LENGTH)
        sector.sector_id = sector_id

        self.port.write('00%02X0000' % sector_index)

    def step_fdc_write_sector(self, req_args):
        assert len(req_args) == 1

        sector_index = int(req_args[0], 10)
        sector = self.disk.sectors[sector_index]

        self.port.write('00%02X0000' % sector_index)

        data = self.read(Sector.DATA_LENGTH)
        sector.data = data

        self.port.write('00%02X0000' % sector_index)

    def step_fdc_read_sector(self, req_args):
        assert len(req_args) == 1

        sector_index = int(req_args[0], 10)
        sector = self.disk.sectors[sector_index]

        response = '00%02X0000' % sector_index
        self.port.write(response)

        wait_value = self.read(1)
        assert wait_value == '\r'

        self.port.write(sector.data)

    def read_fdc_request(self):
        req_cmd = None
        req_argstr = ''

        while True:
            c = self.read(1)
            if req_cmd and c == '\r':
                break

            if c == '\r':
                continue

            if req_cmd:
                req_argstr += c
            else:
                req_cmd = c

        if req_argstr:
            req_args = req_argstr.split(',')
        else:
            req_args = []

        return req_cmd, req_args

    def read(self, count=1, ignore_zeroes=False):
        b = ''

        while len(b) != count:
            c = self.port.read()

            if ignore_zeroes and c == '\x00':
                continue

            if c != '':
                b += c

        return b
