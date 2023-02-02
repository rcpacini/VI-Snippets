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
COLOR_TABLE_8BITx = [
0xFFFFFF00, 0xFFFFCC00, 0xFFFF9900, 0xFFFF6600, 0xFFFF3300, 0xFFFF0000, 0xFFCCFF00, 0xFFCCCC00,
0xFFCC9900, 0xFFCC6600, 0xFFCC3300, 0xFFCC0000, 0xFF99FF00, 0xFF99CC00, 0xFF999900, 0xFF996600,
0xFF993300, 0xFF990000, 0xFF66FF00, 0xFF66CC00, 0xFF669900, 0xFF666600, 0xFF663300, 0xFF660000,
0xFF33FF00, 0xFF33CC00, 0xFF339900, 0xFF336600, 0xFF333300, 0xFF330000, 0xFF00FF00, 0xFF00CC00,
0xFF009900, 0xFF006600, 0xFF003300, 0xFF000000, 0xCCFFFF00, 0xCCFFCC00, 0xCCFF9900, 0xCCFF6600,
0xCCFF3300, 0xCCFF0000, 0xCCCCFF00, 0xCCCCCC00, 0xCCCC9900, 0xCCCC6600, 0xCCCC3300, 0xCCCC0000,
0xCC99FF00, 0xCC99CC00, 0xCC999900, 0xCC996600, 0xCC993300, 0xCC990000, 0xCC66FF00, 0xCC66CC00,
0xCC669900, 0xCC666600, 0xCC663300, 0xCC660000, 0xCC33FF00, 0xCC33CC00, 0xCC339900, 0xCC336600,
0xCC333300, 0xCC330000, 0xCC00FF00, 0xCC00CC00, 0xCC009900, 0xCC006600, 0xCC003300, 0xCC000000,
0x99FFFF00, 0x99FFCC00, 0x99FF9900, 0x99FF6600, 0x99FF3300, 0x99FF0000, 0x99CCFF00, 0x99CCCC00,
0x99CC9900, 0x99CC6600, 0x99CC3300, 0x99CC0000, 0x9999FF00, 0x9999CC00, 0x99999900, 0x99996600,
0x99993300, 0x99990000, 0x9966FF00, 0x9966CC00, 0x99669900, 0x99666600, 0x99663300, 0x99660000,
0x9933FF00, 0x9933CC00, 0x99339900, 0x99336600, 0x99333300, 0x99330000, 0x9900FF00, 0x9900CC00,
0x99009900, 0x99006600, 0x99003300, 0x99000000, 0x66FFFF00, 0x66FFCC00, 0x66FF9900, 0x66FF6600,
0x66FF3300, 0x66FF0000, 0x66CCFF00, 0x66CCCC00, 0x66CC9900, 0x66CC6600, 0x66CC3300, 0x66CC0000,
0x6699FF00, 0x6699CC00, 0x66999900, 0x66996600, 0x66993300, 0x66990000, 0x6666FF00, 0x6666CC00,
0x66669900, 0x66666600, 0x66663300, 0x66660000, 0x6633FF00, 0x6633CC00, 0x66339900, 0x66336600,
0x66333300, 0x66330000, 0x6600FF00, 0x6600CC00, 0x66009900, 0x66006600, 0x66003300, 0x66000000,
0x33FFFF00, 0x33FFCC00, 0x33FF9900, 0x33FF6600, 0x33FF3300, 0x33FF0000, 0x33CCFF00, 0x33CCCC00,
0x33CC9900, 0x33CC6600, 0x33CC3300, 0x33CC0000, 0x3399FF00, 0x3399CC00, 0x33999900, 0x33996600,
0x33993300, 0x33990000, 0x3366FF00, 0x3366CC00, 0x33669900, 0x33666600, 0x33663300, 0x33660000,
0x3333FF00, 0x3333CC00, 0x33339900, 0x33336600, 0x33333300, 0x33330000, 0x3300FF00, 0x3300CC00,
0x33009900, 0x33006600, 0x33003300, 0x33000000, 0x00FFFF00, 0x00FFCC00, 0x00FF9900, 0x00FF6600,
0x00FF3300, 0x00FF0000, 0x00CCFF00, 0x00CCCC00, 0x00CC9900, 0x00CC6600, 0x00CC3300, 0x00CC0000,
0x0099FF00, 0x0099CC00, 0x00999900, 0x00996600, 0x00993300, 0x00990000, 0x0066FF00, 0x0066CC00,
0x00669900, 0x00666600, 0x00663300, 0x00660000, 0x0033FF00, 0x0033CC00, 0x00339900, 0x00336600,
0x00333300, 0x00330000, 0x0000FF00, 0x0000CC00, 0x00009900, 0x00006600, 0x00003300, 0xEE000000,
0xDD000000, 0xBB000000, 0xAA000000, 0x88000000, 0x77000000, 0x55000000, 0x44000000, 0x22000000,
0x11000000, 0x00EE0000, 0x00DD0000, 0x00BB0000, 0x00AA0000, 0x00880000, 0x00770000, 0x00550000,
0x00440000, 0x00220000, 0x00110000, 0x0000EE00, 0x0000DD00, 0x0000BB00, 0x0000AA00, 0x00008800,
0x00007700, 0x00005500, 0x00004400, 0x00002200, 0x00001100, 0xEEEEEE00, 0xDDDDDD00, 0xBBBBBB00,
0xAAAAAA00, 0x88888800, 0x77777700, 0x55555500, 0x44444400, 0x22222200, 0x11111100, 0x00000000
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
