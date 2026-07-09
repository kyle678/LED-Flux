from engine.utils import Colors, Utils


class TestGetGradient:
    def test_endpoints_match_input_colors(self):
        grad = Utils.getGradient(5, (255, 0, 0), (0, 0, 255))
        assert len(grad) == 5
        assert grad[0] == (255, 0, 0)
        assert grad[-1] == (0, 0, 255)

    def test_zero_and_negative_lengths_return_empty(self):
        assert Utils.getGradient(0, (255, 0, 0), (0, 0, 255)) == []
        assert Utils.getGradient(-3, (255, 0, 0), (0, 0, 255)) == []

    def test_length_one_returns_first_color(self):
        assert Utils.getGradient(1, (255, 0, 0), (0, 0, 255)) == [(255, 0, 0)]


class TestGetMultiGradient:
    def test_length_is_exact_even_with_remainder(self):
        # 3 segments over 100 pixels doesn't divide evenly; remainder pixels
        # must be absorbed, not dropped or appended
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)]
        assert len(Utils.getMultiGradient(100, colors)) == 100

    def test_single_color_fills_strip(self):
        assert Utils.getMultiGradient(4, [(9, 9, 9)]) == [(9, 9, 9)] * 4

    def test_empty_colors_returns_empty(self):
        assert Utils.getMultiGradient(10, []) == []

    def test_wrap_returns_to_first_color(self):
        grad = Utils.getMultiGradient(10, [(255, 0, 0), (0, 0, 255)], wrap=True)
        assert len(grad) == 10
        assert grad[0] == (255, 0, 0)
        assert grad[-1] == (255, 0, 0)


class TestGetAlternatingColors:
    def test_alternates_by_step(self):
        colors = Utils.getAlternatingColors(6, [(1, 1, 1), (2, 2, 2)], step=2)
        assert colors == [(1, 1, 1), (1, 1, 1), (2, 2, 2), (2, 2, 2), (1, 1, 1), (1, 1, 1)]

    def test_single_color_ignores_step(self):
        assert Utils.getAlternatingColors(3, [(5, 5, 5)], step=1) == [(5, 5, 5)] * 3


class TestRotateCopy:
    def test_shifts_right(self):
        assert Utils.rotate_copy([1, 2, 3, 4], 1) == [4, 1, 2, 3]

    def test_wraps_past_full_cycle(self):
        assert Utils.rotate_copy([1, 2, 3], 3) == [1, 2, 3]
        assert Utils.rotate_copy([1, 2, 3], 5) == Utils.rotate_copy([1, 2, 3], 2)

    def test_empty_input(self):
        assert Utils.rotate_copy([], 3) == []


def test_hex_to_rgb():
    assert Colors.hex_to_rgb('#ff6400') == (255, 100, 0)
    assert Colors.hex_to_rgb('00ff00') == (0, 255, 0)
