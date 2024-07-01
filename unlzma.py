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
ERR_LZMA_FILE = 0x02
ERR_UNLZMA    = 0x04
ERR_OUT_FILE  = 0x08


def main():
    if len(sys.argv) not in (2, 3):
        sys.stderr.write(f'Usage: {sys.argv[0]} INPUTFILE [OUTPUTFILE]\n')
        return ERR_USAGE

    try:
        inputFile = sys.stdin.buffer if sys.argv[1] == '-' else open(sys.argv[1], 'rb')
    except OSError:
        sys.stderr.write(f'Error: Unable to open file {sys.argv[1]}\n')
        return ERR_LZMA_FILE

    with inputFile:
        inputData = inputFile.read()

    if not (decompressedData := decompress(inputData)):
        return ERR_UNLZMA

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


def lzma_decompress(data: bytes) -> bytes:
    '''an alternative implementation that works when EOS marker is missing'''
    results = bytearray()
    while 1:
        decompressor = lzma.LZMADecompressor(lzma.FORMAT_AUTO, None, None)
        try:
            chunk = decompressor.decompress(data)
        except lzma.LZMAError:
            if results:
                break
            else:
                raise
        results += chunk
        data = decompressor.unused_data
        if not data:
            break
        if not decompressor.eof:
            raise lzma.LZMAError('Compressed data ended before the end-of-stream marker was reached')
    return bytes(results)


def decompress(data: bytes) -> bytes:
    if data[:4] != b'LZMA':
        return

    compressedSize, decompressedSize = struct.unpack_from('<II', data, 4)
    params, dictSize, _ = struct.unpack_from('<BIQ', data, 12)

    header = struct.pack('<BIQ', params, dictSize, 0xffffffffffffffff)
    payload = header + data[25:25+compressedSize]

    return lzma_decompress(payload)


if __name__ == '__main__':
    exit(main())

