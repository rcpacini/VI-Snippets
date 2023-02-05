from struct import pack, unpack
from collections import namedtuple
from dataclasses import dataclass
import logging
import os
import argparse
import winreg


def cli():
    parser = argparse.ArgumentParser(description="Ryan\'s LabVIEW Package Manager")

    parser.add_argument('action', help='The action to take (e.g. install, remove, etc.)')
    parser.add_argument('file', help='Path to file', nargs='?')
    parser.add_argument("-v", "--verbosity", type=int, choices=[0, 1, 2],
                help="Increase output verbosity")

    args = parser.parse_args()

    if args.action in 'list':
        for k, v in list_labview_dirs().items():
            print(f"{v}: '{k}'")
    else:
        print('error: unknown action %s\n' % args.action)
        parser.print_help()


def list_labview_dirs():
    ''' List installed LabVIEW directories from Windows Registry.
    This checks both x86 and x64 registry keys.
    Results returned as dict(path, [version, version, ...])
    {'path\\to\\labview\\':['22.0', '22.3', 'CurrentVersion']}
    '''
    keys = [
            r'SOFTWARE\\WOW6432Node\\National Instruments\\LabVIEW',
            r'SOFTWARE\\National Instruments\\LabVIEW'
    ]
    dirs = {}
    reg_conn = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    for key in keys:
        reg_key = winreg.OpenKey(reg_conn, key)
        for i in range(20):
            try:
                sub_key_name = winreg.EnumKey(reg_key, i)
                sub_key = winreg.OpenKey(reg_key, sub_key_name)
                val = winreg.QueryValueEx(sub_key, "Path")
                dirs.setdefault(val[0], []).append(sub_key_name)
            except EnvironmentError:
                pass
    return dirs


class RSRC_Error(Exception):
    pass

@dataclass
class RSRC_Header:
    rsrc_type : str
    rsrc_creator : str
    info_offset : int

    def __repr__(self):
        return f"{self.__class__.__name__}(type:{self.rsrc_type}, creator:{self.rsrc_creator})"

    def __str__(self):
        return f"{self.__class__.__name__}(type:{self.rsrc_type}, creator:{self.rsrc_creator} at {self.info_offset})"

    def dump(self):
        return f"type:{self.rsrc_type} | creator:{self.rsrc_creator} | info@{self.info_offset:<5}\n"

@dataclass
class RSRC_Block:
    file : str
    name : str
    data : bytes
    index : int
    id_offset : int
    info_offset : int
    data_offset : int

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.name}.{self.index}' size:{len(self.data):>5})"

    def __str__(self):
        return f"{self.__class__.__name__}('{self.name}.{self.index}' size:{len(self.data):>5}" \
            f" at id:{self.id_offset:>5}, info:{self.info_offset:>5}, data:{self.data_offset:>5})"
    
    def dump(self):
        return f"{self.name}.{self.index:<3} = size:{len(self.data):<7} | id@{self.id_offset:<7} | " \
            f"info@{self.info_offset:<7} | data@{self.data_offset:<7}\n"


class RSRC:
    def __init__(self, file=None):
        self.file : str = None
        self.header : RSRC_Header = None
        self.blocks : list[RSRC_Block] = []
        self.filenames : list[str] = []

        if file is not None:
            self.load_rsrc(file)

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.file}' blocks: {len(self.blocks)})"

    def __str__(self):
        return f"{self.__class__.__name__}('{self.file}' blocks: {len(self.blocks)})"
    
    # Functions
    def get_block(self, name, index=0):
        return next((b for b in self.blocks if b.name == name and (index == 0 or b.index == index)), None)
    
    def get_block_data(self, name, index=0):
        return next((b.data for b in self.blocks if b.name == name and (index == 0 or b.index == index)), None)

    def load_rsrc(self, file):
        ''' Loads a resource file (vi, ctl, llb)
        Returns a Tuple(RSRC_HEADER, List(RSRCBlock), List(filenames))
        '''
        self.file = None
        self.header = None
        self.blocks = []
        self.filenames = []

        self.file = os.path.abspath(file)
        if not os.path.exists(self.file):
            raise FileNotFoundError(f'Unable to resolve file path: {file}')

        rsrc = b''
        with open(self.file, mode='rb') as f:
            rsrc = f.read()
        
        RSRC_HEADER = namedtuple('RSRC_HEADER', [
            'rsrc_id',
            'rsrc_version',
            'rsrc_type',
            'rsrc_creator',
            'info_offset',
            'info_size',
            'data_offset',
            'data_size'
        ])

        BLOCK_INFO = namedtuple('RSRC_BLOCK_INFO', [
            'flag1',
            'flag2',
            'flag3',
            'offset',
            'size'
        ])

        BLOCK_ID = namedtuple('RSRC_BLOCK_ID', [
            'name',
            'count',
            'offset'
        ])

        # Read RSRC_HEADER_1
        hdr1 = RSRC_HEADER(*(unpack('>6sH4s4sIIII', rsrc[
            0:
            32
        ])))
        logging.debug(hdr1)
        
        # Read RSRC_HEADER_2
        hdr2 = RSRC_HEADER(*(unpack('>6sH4s4sIIII', rsrc[
                hdr1.info_offset :
                hdr1.info_offset + 32
        ])))
        logging.debug(hdr2)
        
        if hdr1 != hdr2:
            raise RSRC_Error(f'RSRC invalid or corrupt. RSRC Headers are not identical at offset {hdr1.info_offset}.')
        
        self.header = RSRC_Header(
            hdr1.rsrc_type.decode('utf-8'),
            hdr1.rsrc_creator.decode('utf-8'),
            int(hdr1.info_offset)
        )

        # Read BLOCK_INFO_LIST
        info1 = BLOCK_INFO(*(unpack('>iiiII', rsrc[
                hdr1.info_offset + 32 :
                hdr1.info_offset + 32 + 20
        ])))
        logging.debug(info1)

        # Read BLOCK_COUNT
        block_cnt, = unpack('>I', rsrc[
            hdr1.info_offset + info1.offset : 
            hdr1.info_offset + info1.offset + 4
        ])
        block_cnt = int(block_cnt) + 1
        logging.debug('block_cnt=%s', block_cnt)
        if block_cnt > 1000:
            raise RSRC_Error(f'RSRC invalid or corrupt. Block count limit exceeded {block_cnt}.')

        # Read BLOCKs
        fnames_offset = 0
        bid_offset = hdr1.info_offset + info1.offset + 4
        
        for i in range(block_cnt):
            logging.debug('   BLOCK %s', i)
            
            # Read new BLOCK_ID
            bid = BLOCK_ID(*(unpack('>4sII', rsrc[
                bid_offset :
                bid_offset + 12
            ])))
            logging.debug(bid)
            
            binfo_offset = hdr1.info_offset + info1.offset + bid.offset

            for bidx in range(int(bid.count) + 1):
                logging.debug('   BLOCK %s INDEX %s', i, bidx)
                
                # Read next BLOCK_INFO
                binfo = BLOCK_INFO(*(unpack('>iiiII', rsrc[
                    binfo_offset :
                    binfo_offset + 20
                ])))
                logging.debug(binfo)
                
                # Read BLOCK_DATA_LENGTH
                bdata_offset = hdr1.data_offset + binfo.offset
                blen, = unpack('>I', rsrc[
                    bdata_offset :
                    bdata_offset + 4
                ])
                logging.debug('block_length=%s', blen)

                # Append block
                self.blocks.append(
                    # Read BLOCK_DATA
                    RSRC_Block(
                        file,
                        bid.name.decode('utf-8'),
                        rsrc[
                            bdata_offset + 4 :
                            bdata_offset + 4 + int(blen)
                        ],
                        int(bidx),
                        int(bid_offset),
                        int(binfo_offset),
                        int(bdata_offset)
                    )
                )

                # Find fnames offset
                fnames_offset = max(
                    fnames_offset,
                    binfo_offset + 20,
                    bdata_offset + 4 + int(blen)
                )

                # Increment block info offset
                binfo_offset = binfo_offset + 20

            # Increment block id offset
            bid_offset = bid_offset + 12
            
        # Read filenames at end
        fremaining = len(rsrc[fnames_offset:])
        logging.debug('fnames_offset=%s, fnames_remaining=%s', fnames_offset, fremaining)
        foffset = 0
        
        while(fnames_offset > 0 and foffset < fremaining):
            # Read FILENAME_LENGTH
            flength, = unpack('>B', rsrc[
                fnames_offset + foffset :
                fnames_offset + foffset + 1
            ])
            
            # Read FILENAME
            fname, = unpack(f'{flength}s', rsrc[
                fnames_offset + foffset + 1 :
                fnames_offset + foffset + 1 + flength
            ])
            foffset = foffset + 1 + flength

            # Append filename
            self.filenames.append(
                fname.decode('utf-8')
            )
        logging.debug(self.filenames)

    def dump_blocks(self, dest_dir=None):
        if self.file is None:
            raise RSRC_Error('RSRC invalid or corrupt. No RSRC file is loaded.')
        fname, fext = os.path.splitext(os.path.split(self.file)[1])
        fname_fext = f'{fname}_{fext[1:]}'
        if dest_dir is None:
            dest_dir = os.path.join(os.path.split(self.file)[0], fname_fext)
        
        dest_dir = os.path.abspath(dest_dir)
        if not os.path.isdir(dest_dir) or not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        
        for b in self.blocks:
            file = os.path.join(dest_dir, f'{b.name}-{b.index}')
            with open(file, mode='wb') as f:
                f.write(b.data)
        
        file = os.path.join(dest_dir, f'_{fname_fext}.txt')
        with open(file, mode='w') as f:
            f.write('[header]\nrsrc = ')
            f.write(self.header.dump())
            f.write('\n[blocks]\n')
            for b in self.blocks:
                f.write(b.dump())
            f.write('\n[filenames]\n')
            f.write('\n'.join(self.filenames))


from struct import pack, unpack

# Write BITMAP_FILE_HEADER

# Write BITMAP_INFO_HEADER

# Write COLOR_TABLE

# Write PIXEL_DATA

r'''
1. BITMAP_FILE_HEADER - Total 14 bytes Size of the BITMAPFILEHEADER in bytes.
    file_type = b'BM'
        2 bytes A 2 character string value in ASCII to specify a DIB file type.
        It must be 'BM' or '0x42 0x4D' in hexadecimals for modern compatibility reasons.
    file_size = 0
        4 bytes An integer (unsigned) representing entire file size in bytes.
        This value is basically the number of bytes in a BMP image file.
    reserved_1 = 0
    reserved_2 = 0
        2 bytes These 2 bytes are reserved to be utilized by an image processing application to add additional meaningful information.
        It should be initialized to '0' integer (unsigned) value.
    pixel_data_offset = 0
        4 bytes An integer (unsigned) representing the offset of actual pixel data in bytes.
        In nutshell:- it is the number of bytes between start of the file (0) and the first byte of the pixel data.
2. BITMAP_INFO_HEADER - Total 40 bytes Size of the BITMAPINFOHEADER in bytes.
    header_size = 0
        4 bytes An integer (unsigned) representing the size of the header in bytes.
        It should be '40' in decimal to represent BITMAPINFOHEADER header type.
    image_width = width
        4 bytes An integer (signed) representing the width of the final image in pixels.
    image_height = height
        4 bytes An integer (signed) representing the height of the final image in pixels.
    planes = 1
        2 bytes An integer (unsigned) representing the number of color planes of the target device.
        Should be '1' in decimal.
    bits_per_pixel = depth
        2 bytes An integer (unsigned) representing the number of bits (memory) a pixel takes (in pixel data) to represent a color.
    compression = 0
        4 bytes An integer (unsigned) representing the value of compression to use.
        Should be '0' in decimal to represent no-compression (identified by 'BI_RGB').
    image_size = 0
        4 bytes An integer (unsigned) representing the final size of the compressed image.
        Should be '0' in decimal when no compression algorithm is used.
    x_pixels_per_meter = 0
        4 bytes An integer (signed) representing the horizontal resolution of the target device.
        This parameter will be adjusted by the image processing application but should be set to '0' in decimal to indicate no preference.
    y_pixels_per_meter = 0
        4 bytes An integer (signed) representing the verical resolution of the target device (same as the above).
    total_colors = 0
        4 bytes An integer (unsigned) representing the number of colors in the color pallet (size of the color pallet or color table).
        If this is set to '0' in decimal :- 2^BitsPerPixel colors are used.
    important_colors = 0
        4 bytes An integer (unsigned) representing the number of important colors.
        Generally ignored by setting '0' decimal value.
3. COLOR_TABLE - Total 4 bytes per color
    color_table = [0xFF_FF_FF_00, 0x00_00_00_00]
        4 bytes * 2^bits_per_pixel A color as Red, Green, Blue, Alpha bytes times the number of bits_per_pixel depth.
        If the bits_per_pixel is > 8 than the color table is not used.
        If bits_per_pixel == 1: 2 Maximum (4 bytes * 2 = 8 bytes total) for monochromatic image of any two colors defined in the pallet.
        If bits_per_pixel == 4: 16 Maximum (4 bytes * 16 = 64 bytes total) 16 distinct colors can be defined in the pallet.
        If bits_per_pixel == 8: 256 Maximum (4 bytes * 256 = 1024 bytes total) 256 distinct colors can be defined in the pallet.
4. PIXEL_DATA - Total x bytes per pixel
'''

COLOR_TABLE_8BIT = [
0x00FFFFFF, 0x00FFFFCC, 0x00FFFF99, 0x00FFFF66, 0x00FFFF33, 0x00FFFF00, 0x00FFCCFF, 0x00FFCCCC,
0x00FFCC99, 0x00FFCC66, 0x00FFCC33, 0x00FFCC00, 0x00FF99FF, 0x00FF99CC, 0x00FF9999, 0x00FF9966,
0x00FF9933, 0x00FF9900, 0x00FF66FF, 0x00FF66CC, 0x00FF6699, 0x00FF6666, 0x00FF6633, 0x00FF6600,
0x00FF33FF, 0x00FF33CC, 0x00FF3399, 0x00FF3366, 0x00FF3333, 0x00FF3300, 0x00FF00FF, 0x00FF00CC,
0x00FF0099, 0x00FF0066, 0x00FF0033, 0x00FF0000, 0x00CCFFFF, 0x00CCFFCC, 0x00CCFF99, 0x00CCFF66,
0x00CCFF33, 0x00CCFF00, 0x00CCCCFF, 0x00CCCCCC, 0x00CCCC99, 0x00CCCC66, 0x00CCCC33, 0x00CCCC00,
0x00CC99FF, 0x00CC99CC, 0x00CC9999, 0x00CC9966, 0x00CC9933, 0x00CC9900, 0x00CC66FF, 0x00CC66CC,
0x00CC6699, 0x00CC6666, 0x00CC6633, 0x00CC6600, 0x00CC33FF, 0x00CC33CC, 0x00CC3399, 0x00CC3366,
0x00CC3333, 0x00CC3300, 0x00CC00FF, 0x00CC00CC, 0x00CC0099, 0x00CC0066, 0x00CC0033, 0x00CC0000,
0x0099FFFF, 0x0099FFCC, 0x0099FF99, 0x0099FF66, 0x0099FF33, 0x0099FF00, 0x0099CCFF, 0x0099CCCC,
0x0099CC99, 0x0099CC66, 0x0099CC33, 0x0099CC00, 0x009999FF, 0x009999CC, 0x00999999, 0x00999966,
0x00999933, 0x00999900, 0x009966FF, 0x009966CC, 0x00996699, 0x00996666, 0x00996633, 0x00996600,
0x009933FF, 0x009933CC, 0x00993399, 0x00993366, 0x00993333, 0x00993300, 0x009900FF, 0x009900CC,
0x00990099, 0x00990066, 0x00990033, 0x00990000, 0x0066FFFF, 0x0066FFCC, 0x0066FF99, 0x0066FF66,
0x0066FF33, 0x0066FF00, 0x0066CCFF, 0x0066CCCC, 0x0066CC99, 0x0066CC66, 0x0066CC33, 0x0066CC00,
0x006699FF, 0x006699CC, 0x00669999, 0x00669966, 0x00669933, 0x00669900, 0x006666FF, 0x006666CC,
0x00666699, 0x00666666, 0x00666633, 0x00666600, 0x006633FF, 0x006633CC, 0x00663399, 0x00663366,
0x00663333, 0x00663300, 0x006600FF, 0x006600CC, 0x00660099, 0x00660066, 0x00660033, 0x00660000,
0x0033FFFF, 0x0033FFCC, 0x0033FF99, 0x0033FF66, 0x0033FF33, 0x0033FF00, 0x0033CCFF, 0x0033CCCC,
0x0033CC99, 0x0033CC66, 0x0033CC33, 0x0033CC00, 0x003399FF, 0x003399CC, 0x00339999, 0x00339966,
0x00339933, 0x00339900, 0x003366FF, 0x003366CC, 0x00336699, 0x00336666, 0x00336633, 0x00336600,
0x003333FF, 0x003333CC, 0x00333399, 0x00333366, 0x00333333, 0x00333300, 0x003300FF, 0x003300CC,
0x00330099, 0x00330066, 0x00330033, 0x00330000, 0x0000FFFF, 0x0000FFCC, 0x0000FF99, 0x0000FF66,
0x0000FF33, 0x0000FF00, 0x0000CCFF, 0x0000CCCC, 0x0000CC99, 0x0000CC66, 0x0000CC33, 0x0000CC00,
0x000099FF, 0x000099CC, 0x00009999, 0x00009966, 0x00009933, 0x00009900, 0x000066FF, 0x000066CC,
0x00006699, 0x00006666, 0x00006633, 0x00006600, 0x000033FF, 0x000033CC, 0x00003399, 0x00003366,
0x00003333, 0x00003300, 0x000000FF, 0x000000CC, 0x00000099, 0x00000066, 0x00000033, 0x00EE0000,
0x00DD0000, 0x00BB0000, 0x00AA0000, 0x00880000, 0x00770000, 0x00550000, 0x00440000, 0x00220000,
0x00110000, 0x0000EE00, 0x0000DD00, 0x0000BB00, 0x0000AA00, 0x00008800, 0x00007700, 0x00005500,
0x00004400, 0x00002200, 0x00001100, 0x000000EE, 0x000000DD, 0x000000BB, 0x000000AA, 0x00000088,
0x00000077, 0x00000055, 0x00000044, 0x00000022, 0x00000011, 0x00EEEEEE, 0x00DDDDDD, 0x00BBBBBB,
0x00AAAAAA, 0x00888888, 0x00777777, 0x00555555, 0x00444444, 0x00222222, 0x00111111, 0x00000000
]
COLOR_TABLE_4BIT = [
0x00FFFFFF, 0x00FFFF00, 0x00000080, 0x00FF0000, 0x00FF00FF, 0x00800080, 0x000000FF, 0x0000FFFF,
0x0000FF00, 0x00008000, 0x00800000, 0x00808000, 0x00C0C0C0, 0x00808080, 0x00008080, 0x00000000
]
COLOR_TABLE_1BIT = [0x00FFFFFF, 0x00000000]

def write_bmp(file, img_bytes, width=32, height=32, depth=1):
    # 1. BITMAP_FILE_HEADER (14 bytes)
    file_type = b'BM'
    file_size = 0
    reserved_1 = 0
    reserved_2 = 0
    pixel_data_offset = 0
    # 2. BITMAP_INFO_HEADER (40 bytes)
    header_size = 40
    image_width = width
    image_height = height * -1 # https://stackoverflow.com/questions/26144955/after-writing-bmp-file-image-is-flipped-upside-down
    planes = 1
    bits_per_pixel = depth
    compression = 0
    image_size = 0
    x_pixels_per_meter = 0
    y_pixels_per_meter = 0
    total_colors = 0
    important_colors = 0
    # 3. COLOR_TABLE
    color_table = []
    if bits_per_pixel == 1:
        total_colors = 2
        color_table = COLOR_TABLE_1BIT
    elif bits_per_pixel == 4:
        total_colors = 16
        color_table = COLOR_TABLE_4BIT
    elif bits_per_pixel == 8:
        total_colors = 256
        color_table = COLOR_TABLE_8BIT
    # 4. PIXEL_DATA
    pixel_data_offset = 14 + header_size + len(color_table) * 4
    pixel_data = img_bytes
    # ToDo - account for odd byte scan line offsets
    file_size = pixel_data_offset + len(pixel_data)
    # Pack BMP file
    with open(file, mode='wb') as f:
        f.write(pack('<2sIHHI',
            file_type,
            file_size,
            reserved_1,
            reserved_2,
            pixel_data_offset
        ))
        f.write(pack('<IiiHHIIIIII',
            header_size,
            image_width,
            image_height,
            planes,
            bits_per_pixel,
            compression,
            image_size,
            x_pixels_per_meter,
            y_pixels_per_meter,
            total_colors,
            important_colors
        ))
        f.write(b''.join([pack('<I', c) for c in color_table]))
        f.write(pixel_data)
