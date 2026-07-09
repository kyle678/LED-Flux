import time

from abc import ABC, abstractmethod

from engine.utils import Colors, Utils

class BaseAnimation(ABC):
    def __init__(self,
                 animation_type,
                 name="new animation",
                 num_pixels=10,
                 brightness=1,
                 start_index=0,
                 loop_duration=5,
                 target_fps=30,
                 colors=[(255, 100, 0), (0, 255, 100), (100, 0, 255)],
                 hide=False,
                 wrap=True
                 ):

        self.hide = hide
        self.wrap = wrap
        self.name = name
        self.animation_type = animation_type
        self.colors = colors
        self.color = self.colors[0] if self.colors else (255, 255, 255)
        self.num_pixels = num_pixels
        self.start_index = start_index
        self.loop_duration = loop_duration
        self.target_fps = target_fps
        self.update_interval = 1.0 / target_fps
        self.last_update = 0
        self.brightness = brightness
        self.pixels = [Colors.BLACK for _ in range(num_pixels)]
        self.base_pixels = self.pixels.copy()
        self.start_time = time.monotonic()
        self.blank = [Colors.BLACK for _ in range(num_pixels)]

    def ready_to_update(self):
        now = time.monotonic()
        if now - self.last_update >= self.update_interval:
            self.last_update = now
            return True
        return False
    
    def render_frame(self):
        if self.hide:
            return self.blank
        self.update()
        if self.brightness < 1:
            dimmed_pixels = []
            for pixel in self.pixels:
                dimmed_pixel = [int(c * self.brightness) for c in pixel]
                dimmed_pixels.append(dimmed_pixel)
            return dimmed_pixels
        return self.get_pixels()

    def get_delta_time(self):
        return time.monotonic() - self.start_time
    
    def get_loop_time(self):
        return (self.get_delta_time() % self.loop_duration) / self.loop_duration

    def pixel_to_time_ratio(self):
        return self.get_loop_time()

    def get_cycle_index(self):
        return int(self.pixel_to_time_ratio() * self.num_pixels)

    def get_start_index(self):
        return self.start_index

    def get_pixels(self):
        return self.pixels
    
    @abstractmethod
    def update(self):
        pass

class StaticAnimation(BaseAnimation):
    def __init__(self, animation_type='static', **kwargs):
        super().__init__(animation_type, **kwargs)
        self.setup()

    def setup(self):
        self.pixels = [self.color for _ in range(self.num_pixels)]

    def update(self):
        pass

class RotatingAnimation(BaseAnimation):
    def __init__(self,
                 animation_type='rotating',
                 wrap=True,
                 **kwargs
                ):
        
        super().__init__(animation_type, **kwargs)

        self.wrap = wrap

        self.setup()

    def setup(self):
        if self.wrap:
            self.colors.append(self.colors[0])
        new_pixels = Utils.getMultiGradient(self.num_pixels, self.colors)
        self.pixels = new_pixels
        self.base_pixels = new_pixels.copy()

    def update(self):
        rotate_by = self.get_cycle_index()
        self.pixels = Utils.rotate_copy(self.base_pixels, rotate_by)