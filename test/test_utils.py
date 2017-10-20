from rgkit.render.utils import rgb_to_hex


def test_rgb_to_hex():
    expected_hex = '#ff7f3f'

    assert rgb_to_hex(1, 0.5, 0.25) == expected_hex
    assert rgb_to_hex(
        255, 127, 63, normalized=False) == expected_hex
