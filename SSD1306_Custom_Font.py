#!/usr/bin/env python3
#
# Author: Frederick Altrock frederick.altrock@web.de
# License: cc-by 4.0
# Created: 2025-09-09
#

# CMDS as in the datasheet
_SET_CONTRAST = 0x81 # clear
_SET_ENTIRE_ON = 0xA4
_SET_NORM_INV = 0xA6 # invert pixels
_SET_DISP = 0xAE # on/off
_SET_MEM_ADDR = 0x20 # how the bytearry sequentially sent via i2c/spi is reconstructed in the ssd1306
# Note that memore is organized via 3 pointers in the ssd1306: (page_idx, row_idx, col_idx)
_SET_COL_ADDR = 0x21 # pointer to the column in memory of the ssd1306
_SET_PAGE_ADDR = 0x22 # page pointer to the memory of the ssd1306 (memory is organized in pages, rows and columns for efficiency. In short 1byte=8bit, thus a page is 8 rows as each byte encodes 8 vertical pixels.
_SET_DISP_START_LINE = 0x40 # line pointer
_SET_SEG_REMAP = 0xA0
_SET_MUX_RATIO = 0xA8
_SET_IREF_SELECT = 0xAD
_SET_COM_OUT_DIR = 0xC0
_SET_DISP_OFFSET = 0xD3
_SET_COM_PIN_CFG = 0xDA
_SET_DISP_CLK_DIV = 0xD5
_SET_PRECHARGE = 0xD9
_SET_VCOM_DESEL = 0xDB
_SET_CHARGE_PUMP = 0x8D

WIDTH = 128
HEIGHT = 64


class SSD1306:
    def __init__(self,i2c,width=WIDTH, height=HEIGHT) -> None:
        self.i2c = i2c
        devices = i2c.scan()
        if 0x3C not in devices:
            print("SSD1306 was not recognized by i2c")
        self.pages = HEIGHT // 8
        self.buffer = bytearray(self.pages * WIDTH)
        self.width = width
        self.height = height
        self.fonts = {}
        self.active_font = None

        for cmd in (
            _SET_DISP,  # display off
            # address setting
            _SET_MEM_ADDR, 0x00,  # horizontal
            # resolution and layout
            _SET_DISP_START_LINE,  # start at line 0
            _SET_SEG_REMAP | 0x01,  # column addr 127 mapped to SEG0
            _SET_MUX_RATIO,
            HEIGHT - 1,
            _SET_COM_OUT_DIR | 0x08,  # vertical orientation
            _SET_DISP_OFFSET, 0x00,   # don't shift display content
            _SET_COM_PIN_CFG, 0x12,
            # timing and driving scheme
            _SET_DISP_CLK_DIV, 0x80,
            _SET_PRECHARGE, 0xF1,
            _SET_VCOM_DESEL, 0x30,  # 0.83*Vcc
            # display
            _SET_CONTRAST, 0xFF,# maximum
            _SET_ENTIRE_ON,  # output follows RAM contents
            _SET_NORM_INV,  # not inverted
            _SET_IREF_SELECT, 0x30,  # enable internal IREF during display on
            # charge pump
            _SET_CHARGE_PUMP, 0x14,
            _SET_DISP | 0x01,  # display on
        ): 
            self._write_cmd(cmd)
        
    def _write_cmd(self,cmd):
        self.i2c.writeto_mem(0x3C, int.from_bytes(b'\x80','big'), bytes([cmd]))   

    def _write_data(self):
        self.i2c.writeto_mem(0x3C, int.from_bytes(b'\x40','big'), self.buffer)

    def poweroff(self):
            self._write_cmd(_SET_DISP)

    def poweron(self):
        self._write_cmd(_SET_DISP | 0x01)

    def setContrast(self, contrast):
        self._write_cmd(_SET_CONTRAST)
        self._write_cmd(contrast)

    def invert(self, invert):
        self._write_cmd(_SET_NORM_INV | (invert & 1))

    def show(self):
        x0 = 0
        x1 = WIDTH - 1
        self._write_cmd(_SET_COL_ADDR)
        self._write_cmd(x0)
        self._write_cmd(x1)
        self._write_cmd(_SET_PAGE_ADDR)
        self._write_cmd(0)
        self._write_cmd(self.pages - 1)
        self._write_data()

    def fill(self,c):        
        if c == 0:
            self.buffer[:] = b"\x00"* len(self.buffer)
        else:
            self.buffer[:] = b"\xFF"* len(self.buffer)

    def text(self, text, x, y):
        """
        Draws text using a pre-paged font for maximum efficiency.
        This function becomes a series of memory copies (blits).
        """
        current_x = x
        font = self.active_font
        if font is None:
            print("You have to first select a font. Provde a .pf file, put it in the same directory as this script and call 'load_font()' with the basename of the file.")
            return
        default_char_def = font['characters'][font['default_character']]
        # Calculate the vertical page and the bit-shift offset within the page
        start_page = y // 8
        y_offset_in_page = y % 8

        for char in text:
            char_def = font['characters'].get(char, default_char_def)
            char_width = char_def['char_width']
            paged_data = char_def['paged_data']

            # Loop through each page-slice of the pre-converted character data
            for page_offset, page_slice in enumerate(paged_data):
                dest_page = start_page + page_offset
                
                # Loop through each vertical column (byte) of the page-slice
                for i, src_byte in enumerate(page_slice):
                    dest_x = current_x + i
                    if not (0 <= dest_x < self.width):
                        continue

                    if y_offset_in_page == 0:
                        # y is perfectly page-aligned
                        if 0 <= dest_page < (self.pages):
                            self.buffer[dest_x + dest_page * self.width] |= src_byte
                    else:
                        # y is not page-aligned: We need to write to two pages for each byte.
                        # Part 1: The portion of the byte in the current destination page
                        if 0 <= dest_page < (self.pages):
                            self.buffer[dest_x + dest_page * self.width] |= (src_byte << y_offset_in_page)
                        
                        # Part 2: The portion that spills over into the page below
                        if 0 <= (dest_page + 1) < (self.pages):
                            self.buffer[dest_x + (dest_page + 1) * self.width] |= (src_byte >> (8 - y_offset_in_page))
            
            current_x += char_width

    def _convert_char_to_paged_format(self, char_def, font_data):
        """
        Helper function to convert a single character's bitmap from a
        horizontal scanline format to the vertical, paged format needed
        by the SSD1306.
        """
        width = char_def['char_width']
        height = char_def['char_height']
        start_index = char_def['start_index']
        
        # Calculate how many 8-pixel-high pages this character will span
        num_pages = (height + 7) // 8
        
        # Create a list of bytearrays, one for each page slice of the character.
        # Each bytearray will be `width` bytes long.
        paged_data = [bytearray(width) for _ in range(num_pages)]
        
        width_in_bytes = (width + 7) // 8 # Bytes per row in source data

        # Iterate through every source pixel of the character bitmap
        for y in range(height):
            for x in range(width):
                # Find the source byte and bit for the current pixel
                src_byte_index = start_index + (y * width_in_bytes) + (x // 8)
                src_bit_index = 7 - (x % 8)
                
                # If the source pixel is set...
                if (font_data[src_byte_index] >> src_bit_index) & 1:
                    # ...calculate the destination page and bit in our paged format
                    dest_page_index = y // 8
                    dest_bit_mask = 1 << (y % 8)
                    
                    # Set the corresponding bit in our paged data structure
                    paged_data[dest_page_index][x] |= dest_bit_mask
                    
        return paged_data

    def load_fonts(self, *font_names):
        for font_name in font_names:
            self.load_font(font_name)

    def load_font(self, font_name):
        """
        Loads a .pf font and pre-converts all character data into the
        SSD1306's native page layout for extremely fast rendering.
        """
        try:
            with open(f'{font_name}.pf', 'rb') as f:
                # --- This part is the same as your original loader ---
                header = f.read(4)
                if len(header) < 4 or header[0] != ord('P') or header[1] != ord('F'):
                    print(f'{font_name}.pf has an unknown file format')
                    return None
                
                font = {
                    'name': font_name,
                    'default_character': chr(header[2]),
                    'character_count': header[3],
                    'characters': {},
                }
                
                remaining_header_size = font['character_count'] * 5
                header_data = f.read(remaining_header_size)
                
                index = 0
                for i in range(font["character_count"]):
                    char = chr(header_data[index])
                    char_width = header_data[index + 1]
                    char_height = header_data[index + 2]
                    start_index = header_data[index + 3] + header_data[index + 4] * 256
                    font['characters'][char] = {
                        'char_width': char_width,
                        'char_height': char_height,
                        'start_index': start_index
                    }
                    index += 5
                
                raw_font_data = f.read()
                # --- End of original loading part ---

                # --- NEW: Convert all character data to paged format ---
                for char, char_def in font['characters'].items():
                    char_def['paged_data'] = self._convert_char_to_paged_format(char_def, raw_font_data)
                    # We no longer need the start_index
                    del char_def['start_index']

                self.fonts[font_name] = font
                if self.active_font is None:
                    self.active_font = self.fonts[font_name]

        except OSError as e:
            print(f"Error loading font {font_name}.pf: {e}")
            return None
        
    def select_font(self,font_name):
        try:
            self.active_font=self.fonts[font_name]
        except:
            print(f"Font {font_name} was not selected. Is it loaded?")

    def draw_pixel(self, x, y, color=1):
        """
        Draw a single pixel at coordinates (x, y) in the buffer.
        color = 1 -> set pixel
        color = 0 -> clear pixel
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return  # Pixel out of bounds

        page = y // 8
        bit_mask = 1 << (y % 8)
        index = x + page * self.width

        if color:
            self.buffer[index] |= bit_mask
        else:
            self.buffer[index] &= ~bit_mask



