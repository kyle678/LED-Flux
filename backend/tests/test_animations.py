import time

from engine.animations.animations import RotatingAnimation, StaticAnimation


def test_rotating_gradient_spans_strip():
    anim = RotatingAnimation(num_pixels=10, colors=[[255, 0, 0], [0, 0, 255]], wrap=False)
    assert len(anim.get_pixels()) == 10
    assert anim.get_pixels()[0] == (255, 0, 0)


def test_rotating_rotates_with_time():
    anim = RotatingAnimation(num_pixels=10, loop_duration=10,
                             colors=[[255, 0, 0], [0, 0, 255]], wrap=False)
    first = anim.get_pixels()[0]
    # Pretend half a loop has elapsed: the frame should be rotated by 5
    anim.start_time = time.monotonic() - 5.0
    anim.update()
    assert anim.get_pixels()[5] == first


def test_render_frame_dims_pixels():
    anim = StaticAnimation(num_pixels=4, brightness=0.5, colors=[(200, 100, 50)])
    assert anim.render_frame() == [[100, 50, 25]] * 4


def test_hidden_animation_renders_blank_exactly_once():
    anim = StaticAnimation(num_pixels=4, hide=True, colors=[(255, 0, 0)])
    assert anim.ready_to_update() is True
    assert anim.render_frame() == [(0, 0, 0)] * 4
    # The blank segment never changes, so it must not keep re-rendering
    assert anim.ready_to_update() is False


def test_request_render_forces_another_pass():
    anim = StaticAnimation(num_pixels=4, colors=[(255, 0, 0)])
    assert anim.ready_to_update() is True
    assert anim.ready_to_update() is False
    anim.request_render()
    assert anim.ready_to_update() is True
