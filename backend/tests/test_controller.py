import pytest

from engine.animations.animations import StaticAnimation
from engine.controller import Controller
from tests.conftest import lit


class TestCropping:
    def test_animation_overrunning_strip_is_cropped(self, controller):
        controller.add_animation(StaticAnimation(num_pixels=8, start_index=5, colors=[(255, 0, 0)]))
        controller.update()
        assert lit(controller) == [5, 6, 7, 8, 9]

    def test_negative_start_index_is_cropped(self, controller):
        controller.add_animation(StaticAnimation(num_pixels=5, start_index=-3, colors=[(255, 0, 0)]))
        controller.update()
        assert lit(controller) == [0, 1]

    def test_animation_entirely_off_strip_lights_nothing(self, controller):
        controller.add_animation(StaticAnimation(num_pixels=5, start_index=50, colors=[(255, 0, 0)]))
        controller.update()
        assert lit(controller) == []


class TestPowerAndPause:
    def test_update_is_noop_while_inactive(self, controller):
        controller.add_animation(StaticAnimation(num_pixels=10, colors=[(255, 0, 0)]))
        controller.set_active(False)
        shows = controller.pixels.show_count
        controller.update()
        assert controller.pixels.show_count == shows
        assert lit(controller) == []

    def test_power_on_rerenders_blanked_strip(self, controller):
        controller.add_animation(StaticAnimation(num_pixels=10, colors=[(255, 0, 0)]))
        controller.update()
        # Blank the buffer the way handle_power off does
        controller.set_power(False)
        controller[:] = [(0, 0, 0) for _ in range(controller.num_pixels)]
        controller.show()
        assert lit(controller) == []

        controller.set_power(True)
        controller.update()
        assert lit(controller) == list(range(10))

    def test_set_power_true_also_activates(self, controller):
        controller.set_active(False)
        controller.set_power(True)
        assert controller.active is True


class TestRenderEfficiency:
    def test_static_renders_once_then_stops_pushing(self, controller):
        controller.add_animation(StaticAnimation(num_pixels=10, colors=[(255, 0, 0)]))
        controller.update()
        shows = controller.pixels.show_count
        for _ in range(5):
            controller.update()
        assert controller.pixels.show_count == shows


def test_set_brightness_updates_strip(controller):
    controller.set_brightness(0.5)
    assert controller.brightness == 0.5
    assert controller.pixels.brightness == 0.5


def test_clear_drops_animations_and_blanks(controller):
    controller.add_animation(StaticAnimation(num_pixels=10, colors=[(255, 0, 0)]))
    controller.update()
    controller.clear()
    assert controller.animations == []
    assert controller.config is None
    assert lit(controller) == []


def test_unsupported_pin_raises():
    with pytest.raises(ValueError):
        Controller(num_pixels=10, pin=13)
