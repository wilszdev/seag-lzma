#!/usr/bin/env python3

# seag-lzma
# Copyright (C) 2024 wilszdev
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import lzma
import struct
import sys


ERR_OK        = 0x00
ERR_USAGE     = 0x01
ERR_IN_FILE   = 0x02
ERR_LZMA      = 0x04
ERR_OUT_FILE  = 0x08


def main():
    if len(sys.argv) not in (2, 3):
        sys.stderr.write(f'Usage: {sys.argv[0]} INPUTFILE [OUTPUTFILE]\n')
        return ERR_USAGE

    try:
        inputFile = sys.stdin.buffer if sys.argv[1] == '-' else open(sys.argv[1], 'rb')
    except OSError:
        sys.stderr.write(f'Error: Unable to open file {sys.argv[1]}\n')
        return ERR_IN_FILE

    with inputFile:
        inputData = inputFile.read()

    if not (decompressedData := compress(inputData)):
        return ERR_LZMA

    try:
        outputFile = sys.stdout.buffer if len(sys.argv) == 2 else open(sys.argv[2], 'wb')
    except OSError:
        sys.stderr.write(f'Error: Unable to open file {sys.argv[2]} for writing\n')
        return ERR_OUT_FILE

    with outputFile:
        writeCount = outputFile.write(decompressedData)

    if writeCount != len(decompressedData):
        sys.stderr.write(f'Error: Failed to write all data to file {sys.argv[2]}\n')
        return ERR_OUT_FILE

    return ERR_OK


def compress(data: bytes) -> bytes:
    dictSize = 0x10000
    header = struct.pack('<B3I', 0x5d, dictSize, len(data), len(data))

    filters = [{
            "id": lzma.FILTER_LZMA1,
            "dict_size": dictSize,
    }]
    compressed = lzma.compress(data, format=lzma.FORMAT_RAW, filters=filters)

    payload = header + compressed

    return b'LZMA' + struct.pack('<II', len(payload), len(data)) + payload


if __name__ == '__main__':
    exit(main())

