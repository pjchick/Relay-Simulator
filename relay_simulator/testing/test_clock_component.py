"""Unit tests for Clock component."""

from components.clock import Clock


def test_clock_color_presets():
    clock = Clock("clock001", "page001")

    # Default should be red preset
    assert clock.properties.get('color') == 'red'
    assert clock.properties.get('on_color') == (255, 0, 0)
    assert clock.properties.get('off_color') == (64, 0, 0)

    clock.set_color('green')
    assert clock.properties['color'] == 'green'
    assert clock.properties['on_color'] == (0, 255, 0)
    assert clock.properties['off_color'] == (0, 64, 0)

    clock.set_color('blue')
    assert clock.properties['color'] == 'blue'
    assert clock.properties['on_color'] == (0, 0, 255)
    assert clock.properties['off_color'] == (0, 0, 64)
