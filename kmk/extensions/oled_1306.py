import adafruit_ssd1306

from kmk.extensions import Extension
from kmk.handlers.stock import passthrough as handler_passthrough
from kmk.keys import make_key


class DisplayOLED(Extension):
    I2C_ADDRESS = 0x3C

    def __init__(
        self, i2c, scenes, *, width=128, height=64, flip=False, address=I2C_ADDRESS
    ):
        self._i2c_address = address
        self._i2c_bus = i2c
        self._width = width
        self._height = height
        self._display = adafruit_ssd1306.SSD1306_I2C(width, height, i2c, addr=address)
        self._scenes = scenes
        self._current_scene = 0
        self._redraw_forced = False
        self._asleep = False

        if flip:
            self._display.rotate(180)

        make_key(
            names=('OLED_NXT',),
            on_press=self._tb_next_scene,
            on_release=handler_passthrough,
        )

        make_key(
            names=('OLED_PRV',),
            on_press=self._tb_prev_scene,
            on_release=handler_passthrough,
        )

        make_key(
            names=('OLED_TOG',),
            on_press=self._tb_toggle,
            on_release=handler_passthrough,
        )

    def during_bootup(self, keyboard):
        self._redraw_forced = True
        return

    def before_matrix_scan(self, keyboard):
        pass

    def after_matrix_scan(self, sandbox):
        pass

    def before_hid_send(self, sandbox):
        pass

    def after_hid_send(self, sandbox):
        if self._asleep:
            return

        scene = self._get_active_scene()
        if self._redraw_forced or scene.is_redraw_needed(sandbox):
            if self._redraw_forced:
                scene.forced_draw(self, self._display, sandbox)
            else:
                scene.draw(self, self._display, sandbox)
            self._display.show()
            self._redraw_forced = False
        return

    def on_runtime_enable(self, keyboard):
        pass

    def on_runtime_disable(self, keyboard):
        pass

    def on_powersave_enable(self, keyboard):
        pass

    def on_powersave_disable(self, sandbox):
        pass

    def _get_active_scene(self):
        if len(self._scenes) > self._current_scene:
            return self._scenes[self._current_scene]

    def _tb_next_scene(self, *args, **kwargs):
        self._current_scene += 1
        if self._current_scene >= len(self._scenes):
            self._current_scene = 0
        self._redraw_forced = True

    def _tb_prev_scene(self, *args, **kwargs):
        self._current_scene -= 1
        if self._current_scene < 0:
            self._current_scene = len(self._scenes) - 1
        self._redraw_forced = True

    def _tb_toggle(self, *args, **kwargs):
        if self._asleep:
            self._asleep = False
            self._redraw_forced = True
        else:
            self._display.fill(0)
            self._display.show()
            self._asleep = True


class DisplayScene:
    def is_redraw_needed(self, sandbox):
        raise NotImplementedError

    def forced_draw(self, oled, display, sandbox):
        self.draw(oled, display, sandbox)

    def draw(self, oled, display, sandbox):
        raise NotImplementedError


class LogoScene(DisplayScene):
    def __init__(self, byte_const):
        self._byte_const = byte_const

    def is_redraw_needed(self, sandbox):
        return False

    def draw(self, oled, display, sandbox):
        length = int(oled._width * oled._height / 8)
        img_bytes = self._byte_const.to_bytes(length, 'big')
        for x in range(0, length):
            display.buf[x] = img_bytes[x]


class KeypressesScene(DisplayScene):
    def __init__(self, matrix_width, matrix_height, split=False):
        # todo:these parameters could be autodetected
        self._matrix_width = matrix_width
        self._matrix_height = matrix_height
        self._split = split
        self._x = 0
        self._y = 0
        self._size = 6

    def is_redraw_needed(self, sandbox):
        if sandbox.matrix_update or sandbox.secondary_matrix_update:
            return True
        return False

    def forced_draw(self, oled, display, sandbox):
        display.fill(0)
        full_width = self._matrix_width * self._size + self._size
        if self._split:
            full_width += 2 * self._size
        full_height = self._matrix_height * self._size + self._size
        self._x = int((oled._width - full_width) / 2)
        self._y = int((oled._height - full_height) / 2)
        if not self._split:
            display.rect(self._x, self._y, full_width, full_height, 1)
        else:
            half_width = int(self._matrix_width * self._size / 2)
            display.rect(self._x, self._y, half_width + self._size, full_height, 1)
            display.rect(
                self._x + half_width + 2 * self._size,
                self._y,
                half_width + self._size,
                full_height,
                1,
            )
        return

    def draw(self, oled, display, sandbox):
        if not sandbox.matrix_update and not sandbox.secondary_matrix_update:
            return
        change = sandbox.matrix_update or sandbox.secondary_matrix_update
        # todo: unfortunately there is a bug with right side - it miss keypresses
        self._draw_key(display, change[1], change[0], change[2])
        return

    def _draw_key(self, display, col, row, status):
        x = int(self._x + col * self._size + self._size / 2)
        if self._split and col >= self._matrix_width / 2:
            x += self._size * 2
        y = int(self._y + row * self._size + self._size / 2)
        display.rect(x, y, self._size, self._size, status, fill=True)
        return


class StatusScene(DisplayScene):
    last_layer = 0

    def is_redraw_needed(self, sandbox):
        if self.last_layer != sandbox.active_layers[0]:
            self.last_layer = sandbox.active_layers[0]
            return True
        return False

    def draw(self, oled, display, sandbox):
        display.fill(0)
        display.text(f"Layer {sandbox.active_layers[0]}", 5, 25, 1)
