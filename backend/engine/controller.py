import neopixel
import board

from engine.animations.animations import *

class Controller:
    def __init__(self, num_pixels=10, brightness=0.2, pin=18):
        self.active = True
        self.power = True
        self.num_pixels = num_pixels
        self.brightness = brightness
        if pin == 18:
            self.pin = board.D18
        elif pin == 21:
            self.pin = board.D21
        else:
            raise ValueError("Unsupported pin number. Use 18 or 21.")
        self.pixels = neopixel.NeoPixel(self.pin, self.num_pixels, brightness=self.brightness, auto_write=False)

        self.clear()

        self.config = None

        self.animations = []

    def is_active(self):
        return self.active
    
    def set_active(self, state):
        self.active = True if state else False

    def is_power(self):
        return self.power

    def set_power(self, state):
        self.power = True if state else False
        self.set_active(self.power)
        if self.power:
            # The power-off handler blanks the strip buffer, so animations
            # that render once (statics) must draw themselves again
            for animation in self.animations:
                animation.request_render()

    def __getitem__(self, key):
        return self.pixels[key]

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            start, stop, step = key.indices(self.num_pixels)
            for i, val in zip(range(start, stop, step), value):
                self.pixels[i] = val
        else:
            self.pixels[key] = value

    def fill(self, color):
        self.pixels.fill(color)

    def show(self):
        self.pixels.show()

    def clear(self):
        self.config = None
        self.animations = []
        self.fill((0, 0, 0))
        self.show()

    def set_brightness(self, brightness):
        self.brightness = brightness
        self.pixels.brightness = brightness
        self.show()

    def update(self):
        if not self.active or not self.power:
            return

        rendered = False
        for animation in self.animations:
            if self.update_animation(animation):
                rendered = True

        # Only push to the strip when a frame actually changed; show() costs
        # ~30us of wire time per pixel, so re-pushing identical frames every
        # loop pass starves command handling
        if rendered:
            self.show()

    def update_animation(self, animation):
        if not animation.ready_to_update():
            return False
        pixels = animation.render_frame()
        start = animation.get_start_index()
        # Clamp to the physical strip so an animation whose start_index
        # plus length overruns (or starts before) the strip is cropped
        # instead of raising IndexError
        first = max(0, -start)
        last = min(len(pixels), self.num_pixels - start)
        for i in range(first, last):
            self[i + start] = pixels[i]
        return True

    def add_animation(self, animation):
        self.animations.append(animation)
