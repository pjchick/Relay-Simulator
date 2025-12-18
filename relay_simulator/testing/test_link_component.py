"""Unit tests for Link component."""

from components.link import Link


def test_link_has_single_pin_and_tab():
    link = Link("link001", "page001")
    assert len(link.pins) == 1

    pin = next(iter(link.pins.values()))
    assert len(pin.tabs) == 1

    tab = next(iter(pin.tabs.values()))
    assert tab.relative_position == (Link.WIDTH_PX / 2, 0)


def test_link_serialization_roundtrip():
    link = Link("link001", "page001")
    link.position = (123, 456)
    link.rotation = 90
    link.link_name = "SIGNAL_A"

    data = link.to_dict()
    assert data["component_type"] == "Link"
    assert data["link_name"] == "SIGNAL_A"
    assert data["rotation"] == 90

    link2 = Link.from_dict(data)
    assert link2.component_id == "link001"
    assert link2.position == (123, 456)
    assert link2.rotation == 90
    assert link2.link_name == "SIGNAL_A"
