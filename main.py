# -*- encoding: utf8 -*-

from os import path

import click
import json

from fdcemu import FDCServer, Disk, Sector
from kh940 import MachineState, parse_memory_dump


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


@click.group()
def cli():
    pass


@cli.command()
@click.argument('port')
@click.argument('statefile')
def emulate(port, statefile):
    if path.exists(statefile):
        with open(statefile, 'r') as f:
            json_data = json.load(f)

        state = MachineState.from_json(json_data)
    else:
        state = MachineState.make_empty()

    disk = _machine_to_disk(state)
    server = FDCServer(port, disk)

    try:
        print 'Emulator started'
        server.run()
    except KeyboardInterrupt:
        print 'Saving disk...'
        new_state = _disk_to_machine(disk)

        with file(statefile, 'w') as f:
            json.dump(new_state.to_json(), f, indent=2)
    finally:
        server.close()


@cli.command('show-pattern')
@click.argument('statefile', type=click.File('r'))
@click.argument('pattern')
def show_pattern(statefile, pattern):
    state = MachineState.from_json(json.load(statefile))

    pattern = state.pattern_with_number(int(pattern))

    if not pattern:
        print 'Pattern not found'
        return

    _show_pattern(pattern)


@cli.command('all-patterns')
@click.argument('statefile', type=click.File('r'))
def all_patterns(statefile):
    state = MachineState.from_json(json.load(statefile))

    for pattern in sorted(state.patterns, key=lambda p: p.pattern_number):
        _show_pattern(pattern)
        print


@cli.group()
def debug():
    pass


@debug.command()
@click.argument('diskfile')
@click.argument('outfile')
def dump(diskfile, outfile):
    disk = Disk(diskfile)
    data = disk.concat_sectors(32)

    state = parse_memory_dump(data)
    state_data = state.serialize()
    assert len(state_data) == len(data)

    for i in range(32):
        disk.sectors[i].data = state_data[i * 1024:(i + 1) * 1024]

    disk.save(outfile)


@debug.command()
@click.argument('diskfile')
def validate(diskfile):
    disk = Disk(diskfile)
    data = disk.concat_sectors(32)

    parse_memory_dump(data)


@debug.command('dump-raw')
@click.argument('diskfile')
@click.argument('outfile')
def dump_raw(diskfile, outfile):
    disk = Disk(diskfile)
    data = disk.concat_sectors(32)

    with open(outfile, 'wb') as f:
        f.write(data)


@debug.command()
@click.argument('statefile')
@click.argument('outfile')
def make(statefile, outfile):
    disk = Disk(outfile)

    state = MachineState.make_empty()
    data = state.serialize()
    print len(data)

    assert len(data) == 32768

    for i in range(32):
        disk.sectors[i].data = data[i * 1024:(i + 1) * 1024]

    disk.save()


@debug.command('extract-machine')
@click.argument('diskfile')
@click.argument('outfile')
def extract_machine(diskfile, outfile):
    disk = Disk(diskfile)
    data = disk.concat_sectors(32)
    state = parse_memory_dump(data)

    json_data = state.to_json()

    with open(outfile, 'w') as f:
        json.dump(json_data, f, indent=2)


@debug.command('create-disk')
@click.argument('statefile')
@click.argument('outfile')
def create_disk(statefile, outfile):
    disk = Disk(outfile)

    with open(statefile, 'r') as f:
        json_data = json.load(f)

    state = MachineState.from_json(json_data)
    data = state.serialize()
    assert len(data) == 32768

    for i in range(32):
        disk.sectors[i].sector_id = '\x01' + '\x00' * (Sector.SECTOR_ID_LENGTH - 1)
        disk.sectors[i].data = data[i * 1024:(i + 1) * 1024]

    disk.save()

if __name__ == '__main__':
    cli()
