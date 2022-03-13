# Display

Stub of module which adds support for displays. Based
on [DisplayIO driver version](https://github.com/adafruit/Adafruit_CircuitPython_DisplayIO_SSD1306/).

### Currently compatible screens

Only SSD1306 OLED screen (tested on 128x64 one)

### Required libraries

`adafruit_displayio_ssd1306.mpy`

`adafruit_display_text`

### Example usage

```python
import busio as io
from kmk.extensions.oled_1306 import DisplayOLED, LogoScene, StatusScene, KeypressesScene
from micropython import const

i2c = io.I2C(scl=board.D3, sda=board.D2, frequency=400000)
layers_names = ['Colemak-DH', 'QWERTY', 'Sym-Nav', 'Number', 'Function']
scenes = [
    BitmapLogoScene("/canvas_raw.bmp"),
    KeypressesScene(matrix_width=16, matrix_height=4, split=True),
    StatusScene(layers_names=layers_names, separate_default_layer=True, rgb_ext=rgb_ext),
]
oled = Display(i2c, scenes, rotation=180)
keyboard.extensions.append(oled)
```

### Keycodes

|Keycode        | Description            |
|---------------|------------------------|
|OLED_TOG       | Turn on/off the screen |
|OLED_NXT       | Next scene             |
|OLED_PRV       | Previous scene         |