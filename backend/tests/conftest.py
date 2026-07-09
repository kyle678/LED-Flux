import sys
import types
from pathlib import Path

# Make the backend package root importable no matter where pytest is run from
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Stub the Pi-only hardware modules before any engine import pulls them in.
# Always override (not setdefault): tests must never drive a real strip.
board = types.ModuleType('board')
board.D18 = 'D18'
board.D21 = 'D21'
sys.modules['board'] = board


class FakeNeoPixel:
    """In-memory stand-in for neopixel.NeoPixel; buf holds the pushed frame."""

    def __init__(self, pin, n, brightness=1.0, auto_write=False):
        self.pin = pin
        self.n = n
        self.brightness = brightness
        self.auto_write = auto_write
        self.buf = [(0, 0, 0)] * n
        self.show_count = 0

    def __setitem__(self, i, value):
        self.buf[i] = tuple(value)

    def __getitem__(self, i):
        return self.buf[i]

    def fill(self, color):
        self.buf = [tuple(color)] * self.n

    def show(self):
        self.show_count += 1


neopixel = types.ModuleType('neopixel')
neopixel.NeoPixel = FakeNeoPixel
sys.modules['neopixel'] = neopixel

import pytest

from engine.controller import Controller


@pytest.fixture
def controller():
    return Controller(num_pixels=10, brightness=0.2, pin=18)


def lit(controller):
    """Indices of pixels on the fake strip that aren't black."""
    return [i for i, p in enumerate(controller.pixels.buf) if p != (0, 0, 0)]
