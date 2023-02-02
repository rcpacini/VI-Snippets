from struct import pack, unpack
from collections import namedtuple
import logging
import os

class RSRCException(Exception):
    pass
# raise CustomError("An error occurred")

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

RSRC_INFO = namedtuple('RSRC_INFO', [
    'flag1',
    'flag2',
    'flag3',
    'offset',
    'size'
])

BLOCK_ID = namedtuple('BLOCK_ID', [
    'name',
    'count',
    'offset'
])

BLOCK = namedtuple('BLOCK', [
    'name',
    'index',
    'data',
    'id_offset',
    'info_offset',
    'data_offset'
])

class RSRC:
    def __init__(self):
        self._file = None
        self._header = None
        self._blocks = []
        self._filenames = []

    # Accessors
    def get_file(self):
        return self._file
    
    def get_header(self):
        return self._header

    def get_block_names(self):
        return [(b.name, b.index) for b in self._blocks]
    
    def get_block(self, name, index=0):
        return next((b for b in self._blocks if b.name == name and (index == 0 or b.index == index)), None)
    
    def get_block_data(self, name, index=0):
        return next((b.data for b in self._blocks if b.name == name and (index == 0 or b.index == index)), None)

    def get_filenames(self):
        return self._filenames

    # Functions
    def load(self, file):
        file = os.path.abspath(file)
        if not os.path.exists(file):
            raise FileNotFoundError(f'Unable to resolve file path: {file}')

        self._file = file
        rsrc = b''
        with open(self._file, mode='rb') as f:
            rsrc = f.read()
        
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
            raise RSRCException(f'RSRC invalid or corrupt. RSRC Headers are not identical at offset {hdr1.info_offset}.')
        self._header = hdr1

        # Read BLOCK_INFO_LIST
        info1 = RSRC_INFO(*(unpack('>iiiII', rsrc[
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
            raise RSRCException(f'RSRC invalid or corrupt. Block count limit exceeded {block_cnt}.')

        # Read BLOCKs
        fnames_offset = 0
        self._blocks = []
        bid_offset = hdr1.info_offset + info1.offset + 4
        
        for i in range(block_cnt):
            logging.debug('--Block %s--', i)
            
            # Read new BLOCK_ID
            bid = BLOCK_ID(*(unpack('>4sII', rsrc[
                bid_offset :
                bid_offset + 12
            ])))
            logging.debug(bid)
            
            binfo_offset = hdr1.info_offset + info1.offset + bid.offset

            for bidx in range(int(bid.count) + 1):
                logging.debug('--Block %s count %s--', i, bidx)
                
                # Read next BLOCK_INFO
                binfo = RSRC_INFO(*(unpack('>iiiII', rsrc[
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
                self._blocks.append(
                    # Read BLOCK_DATA
                    BLOCK(
                        bid.name.decode('utf-8'),
                        bidx,
                        rsrc[
                            bdata_offset + 4 :
                            bdata_offset + 4 + int(blen)
                        ],
                        bid_offset,
                        binfo_offset,
                        bdata_offset
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
        self._filenames = []
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
            self._filenames.append(
                fname.decode('utf-8')
            )
        logging.debug(self._filenames)

    def export_blocks(self, dest_dir=None):
        if self._file is None:
            raise RSRCException('RSRC invalid or corrupt. No RSRC file is loaded.')
        if dest_dir is None:
            fname, fext = os.path.splitext(self._file)
            dest_dir = os.path.join(os.path.split(self._file)[0], f'{fname}_{fext[1:]}')
        
        dest_dir = os.path.abspath(dest_dir)
        if not os.path.isdir(dest_dir) or not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        
        for b in self._blocks:
            file = os.path.join(dest_dir, f'{b.name}-{b.index}')
            with open(file, mode='wb') as f:
                f.write(b.data)
        
        file = os.path.join(dest_dir, '_filenames.txt')
        with open(file, mode='w') as f:
            f.write("\n".join(self._filenames))