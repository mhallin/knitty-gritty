# -*- encoding: utf8 -*-

from os import path

import click
import os
import re
import sys

from fdcemu import FDCServer, Disk
from kh940 import MachineState, parse_memory_dump

import bitmap

IMAGE_RE = re.compile(r'9[0-9][0-9]\.(png|bmp|gif|jpe?g)')


def _machine_to_disk(machine):
    disk = Disk()
    disk.set_concat_sector_data(machine.serialize())

    return disk


def _disk_to_machine(disk):
    data = disk.concat_sectors(32)
    machine = parse_memory_dump(data)

    return machine


def _show_pattern(pattern):
    print 'Pattern #%s: %sx%s' % (pattern.pattern_number, pattern.width, pattern.height)
    print

    for row in pattern.rows:
        print ''.join('█' if b else '░' for b in row)

    print


def _machine_to_folder(state, folder):
    if not path.exists(folder):
        os.makedirs(folder)

    for pattern in state.patterns:
        bitmap.write_pattern(pattern, path.join(folder, '%s.png' % pattern.pattern_number))


def _folder_to_machine(folder):
    if not path.exists(folder):
        return MachineState.make_empty()

    patterns = [bitmap.read_pattern(path.join(folder, f))
                for f in os.listdir(folder) if IMAGE_RE.match(f)]

    return MachineState.with_patterns(patterns)


@click.group()
def cli():
    pass


@cli.command('emulate-folder')
@click.argument('port')
@click.argument('folder')
@click.option('--save/--no-save', 'save_on_exit', default=True, is_flag=True)
@click.option('--save-raw', is_flag=True)
def emulate_folder(port, folder, save_on_exit, save_raw):
    if not path.exists(port):
        print 'ERROR: Port %s not found - is the cable connected?' % port
        sys.exit(1)

    machine = _folder_to_machine(folder)

    print 'Loaded %s patterns:' % len(machine.patterns)

    for pattern in machine.patterns:
        _show_pattern(pattern)

    disk = _machine_to_disk(machine)
    server = FDCServer(port, disk)

    try:
        print 'Emulator started, press Ctrl-C to quit'
        server.run()
    except KeyboardInterrupt:
        if save_on_exit:
            print 'Saving images...'
            new_machine = _disk_to_machine(disk)
            _machine_to_folder(new_machine, folder)

        if save_raw:
            print 'Saving 32kb raw data to %s...' % (folder + '.raw')
            with open(folder + '.raw', 'wb') as f:
                f.write(disk.concat_sectors(32))
    finally:
        server.close()


if __name__ == '__main__':
    cli()
