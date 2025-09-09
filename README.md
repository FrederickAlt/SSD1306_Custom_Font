# SSD1306 Python Driver with Font Support

This is a lightweight, self contained and efficient Micropython driver for SSD1306 OLED displays that support custom fonts. The repo is inspired by [packed-font](https://github.com/mark-gladding/packed-font) however the implementation is completely different. Unlike packed-font, this driver does not call i2c multiple times for every pixel that is drawn and converts the font into a more efficient, pre-paged format. This gives a speedup of factor ~50 if one uses the full screen to display text.

## Installation

In any case you need to copy `SSD1306_Custom_Font.py` to the root or `/lib` directory of your MCU.

---
## Usuage

Copy all .pf files from the fonts you want to use to the root of the device. These can be found in `/font` or after converting them (see Font conversion). Then given `DejaVuSans8.pf`, `DejaVuSans12.pf` and `DejaVuSansMono32.pf` are in the root of the device you may run

```python
from SSD1306_Custom_Font import SSD1306
from machine import I2C

i2c = I2C(sda=0, scl=1)
display=SSD1306(i2c)
display.load_fonts("DejaVuSans8", "DejaVuSans12","DejaVuSansMono32")
display.select_font('DejaVuSansMono32')
display.text('Big', 10, 0)         # 10 pixel x offset
display.select_font('DejaVuSans8')
display.text('This is tiny', 0, 34) # 34 pixel y offset
display.select_font('DejaVuSans12')
display.text('Hello World.', 0, 46) # 46 pixel y offset
display.show()

while True:
    pass
```

### Font conversion

If you want to use `convert_font.py` you will need to have `pillow` installed. This can be done via `pip install pillow`. Then you may run 
```
python convert_font.py DejaVuSans 12
```
where 12 is the desired pixel height on the SSD1306. This should run out of the box on most OS and output a file `DejaVuSans12.pf`. In case you want to know what fonts exist on you system, run `python list_fonts.py`. Then you can run `convert_font.py` with the listed names. Alternatively you can download any *.ttf* file and put it in the same directory as the script. Then run `convert_font.py` and give the basename as the argument.

---

## SSD1306 Class Documentation


### Initialization

#### `__init__(i2c, width=128, height=64)`
Sets up display given an `I2C` object associated with the display.

### `poweroff()`
Turn off the display.

### `poweron()`
Turn on the display.

### `setContrast(contrast)`
Set display contrast (0–255).

### `invert(invert)`
Invert display colors (`1` = invert, `0` = normal).

### `show()`
Update the display with buffer contents.

### `fill(c)`
Fill display (`0` = clear, `1` = fill).

### `draw_pixel(x, y, color=1)`
Set or clear a single pixel.

### `text(text, x, y)`
Render text with the active font.

### `load_fonts(*font_names)`
Load multiple `.pf` fonts.

### `load_font(font_name)`
Load a single `.pf` font.

### `select_font(font_name)`
Select an active font.
