import pytest

from engine import handlers
from tests.conftest import lit


def load_red_scene(controller):
    handlers.handle_config(controller, {'name': 'red', 'animations': [
        {'animation_type': 'static', 'name': 'red', 'num_pixels': 10, 'colors': [[255, 0, 0]]}]})
    controller.update()


class TestBrightness:
    def test_valid_value_applied(self, controller):
        handlers.handle_brightness(controller, {'value': 0.6})
        assert controller.brightness == 0.6

    @pytest.mark.parametrize('bad', [None, 'high', -0.1, 1.5, True])
    def test_invalid_values_ignored(self, controller, bad):
        handlers.handle_brightness(controller, {'value': bad})
        assert controller.brightness == 0.2


class TestAnimation:
    def test_selects_class_by_animation_type(self, controller):
        handlers.handle_animation(controller, {'animation_type': 'static',
                                               'num_pixels': 10, 'color': [255, 0, 0]})
        assert len(controller.animations) == 1
        controller.update()
        assert lit(controller) == list(range(10))

    def test_name_still_selects_class_as_fallback(self, controller):
        handlers.handle_animation(controller, {'name': 'static',
                                               'num_pixels': 10, 'color': [255, 0, 0]})
        assert len(controller.animations) == 1

    def test_unknown_type_is_ignored(self, controller):
        handlers.handle_animation(controller, {'animation_type': 'sparkle'})
        assert controller.animations == []

    def test_invalid_params_dont_blank_running_scene(self, controller):
        load_red_scene(controller)
        handlers.handle_animation(controller, {'animation_type': 'static', 'bogus_field': 1})
        # Construction failed before the strip was cleared, so the running
        # scene must still be intact
        assert len(controller.animations) == 1
        assert lit(controller) == list(range(10))


class TestConfig:
    def test_loads_scene_and_powers_on(self, controller):
        controller.set_power(False)
        handlers.handle_config(controller, {'name': 'scene', 'animations': [
            {'animation_type': 'static', 'name': 'a', 'num_pixels': 5, 'colors': [[255, 0, 0]]},
            {'animation_type': 'rotating', 'name': 'b', 'num_pixels': 5, 'start_index': 5,
             'colors': [[255, 0, 0], [0, 0, 255]]},
        ]})
        assert controller.power is True
        assert controller.active is True
        assert len(controller.animations) == 2

    def test_bad_animation_skipped_rest_loaded(self, controller):
        handlers.handle_config(controller, {'animations': [
            {'animation_type': 'static', 'bogus': True},
            {'animation_type': 'static', 'num_pixels': 5, 'colors': [[0, 255, 0]]},
        ]})
        assert len(controller.animations) == 1

    def test_unknown_type_skipped(self, controller):
        handlers.handle_config(controller, {'animations': [{'animation_type': 'sparkle'}]})
        assert controller.animations == []


class TestPowerAndPause:
    def test_power_off_blanks_and_deactivates(self, controller):
        load_red_scene(controller)
        handlers.handle_power(controller, {'value': 'off'})
        assert controller.power is False
        assert controller.active is False
        assert lit(controller) == []

    def test_unpause_implies_power_on_and_relights(self, controller):
        # Regression for the play-while-off bug: unpausing must power the
        # strip back on and re-render, not leave it dark
        load_red_scene(controller)
        handlers.handle_power(controller, {'value': 'off'})
        handlers.handle_pause(controller, {'value': 'on'})
        assert controller.power is True
        assert controller.active is True
        controller.update()
        assert lit(controller) == list(range(10))

    def test_pause_freezes_without_powering_off(self, controller):
        load_red_scene(controller)
        handlers.handle_pause(controller, {'value': 'off'})
        assert controller.power is True
        assert controller.active is False
        # The last frame stays lit, just frozen
        assert lit(controller) == list(range(10))


def test_get_status_shape(controller):
    assert handlers.handle_get_status(controller) == {
        'active': True,
        'power': True,
        'brightness': 0.2,
        'num_pixels': 10,
        'animations': [],
    }
