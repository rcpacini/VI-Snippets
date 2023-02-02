from struct import pack, unpack
from collections import namedtuple
import logging

import zlib
from math import ceil


def write_png_1bit(file, buf, width=32, height=32, stride=None):
    if stride is None:
        stride = int(ceil(width / 8))
    raw_data = b"".join(
        b'\x00' + buf[span:span + stride] for span in range(0, (height - 1) * stride, stride))

    def png_pack(png_tag, data):
        chunk_head = png_tag + data
        return pack("!I", len(data)) + chunk_head + pack("!I", 0xFFFFFFFF & zlib.crc32(chunk_head))

    with open(file, mode='wb') as f:
        f.write(
            b"".join([
            b'\x89PNG\r\n\x1a\n',
            png_pack(b'IHDR', pack("!2I5B", width, height, 1, 0, 0, 0, 0)),
            png_pack(b'IDAT', zlib.compress(raw_data, 9)),
            png_pack(b'IEND', b'')])
        )

def write_bmp_8bit(file, image_bytes, width=32, height=32):
    bfType = 19778 # Bitmap signature
    bfReserved1 = 0
    bfReserved2 = 0
    bcPlanes = 1
    bcSize = 12
    bcBitCount = 8 # Bit Size 24-bits = 3 bytes
    bfOffBits = 26
    bcWidth = width
    bcHeight = height
    bfSize = 26 + bcWidth * 3 * bcHeight
    # graphics = [(0,0,0)] * bcWidth * bcHeight
    
    with open(file, 'wb') as f:
        # Write BITMAP_FILE_HEADER
        f.write(pack('<HLHHL', 
            bfType, 
            bfSize, 
            bfReserved1, 
            bfReserved2, 
            bfOffBits)) 
        # Write BITMAP_INFO
        f.write(pack('<LHHHH', 
            bcSize, 
            bcWidth, 
            bcHeight, 
            bcPlanes, 
            bcBitCount))
        # Write BITMAP_PIXELS
        # for px in data:
        #     f.write(pack('<BBB', *px))
        f.write(image_bytes)
        for i in range((4 - ((bcWidth * 1) % 4)) % 4):
            f.write(pack('B', 0))




# def main():
#   side = 520
#   b = Bitmap(side, side)
#   for j in range(0, side):
#     b.setPixel(j, j, (255, 0, 0))
#     b.setPixel(j, side-j-1, (255, 0, 0))
#     b.setPixel(j, 0, (255, 0, 0))
#     b.setPixel(j, side-1, (255, 0, 0))
#     b.setPixel(0, j, (255, 0, 0))
#     b.setPixel(side-1, j, (255, 0, 0))
#   b.write('file.bmp')


# if __name__ == '__main__':
#   main()

# import math, struct

# mult4 = lambda n: int(math.ceil(n/4))*4
# mult8 = lambda n: int(math.ceil(n/8))*8
# lh = lambda n: struct.pack("<h", n)
# li = lambda n: struct.pack("<i", n)

# def bmp(rows, w):
#     h, wB = len(rows), int(mult8(w)/8)
#     s, pad = li(mult4(wB)*h+0x20), [0]*(mult4(wB)-wB)
#     s = li(mult4(w)*h+0x20)
#     return (b"BM" + s + b"\x00\x00\x00\x00\x20\x00\x00\x00\x0C\x00\x00\x00" +
#             lh(w) + lh(h) + b"\x01\x00\x01\x00\xff\xff\xff\x00\x00\x00" +
#             b"".join([bytes(row+pad) for row in reversed(rows)]))