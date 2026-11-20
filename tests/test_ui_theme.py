from ui_theme import PALETTES, contrast_ratio, palette_for, load_preferred_theme


def test_light_and_dark_palettes_are_distinct_and_complete():
    light = palette_for("light")
    dark = palette_for("dark")
    assert light["page"] != dark["page"]
    assert light["accent"] and dark["accent"]
    assert light["editor_text"] and dark["editor_text"]
    required = {
        "bg", "surface", "elevated", "fg", "secondary", "muted",
        "blue", "blue_hover", "on_blue", "red", "red_hover", "on_red",
        "border", "focus", "selection", "selection_fg", "disabled",
    }
    assert required.issubset(light)
    assert required.issubset(dark)


def test_system_mode_can_be_resolved_deterministically():
    assert palette_for("system", system_dark=True)["mode"] == "dark"
    assert palette_for("system", system_dark=False)["mode"] == "light"


def test_white_blue_red_text_and_action_contrast():
    for palette in PALETTES.values():
        assert contrast_ratio(palette["fg"], palette["bg"]) >= 7.0
        assert contrast_ratio(palette["on_blue"], palette["blue"]) >= 4.5
        assert contrast_ratio(palette["on_red"], palette["red"]) >= 4.5


def test_invalid_color_is_rejected():
    try:
        contrast_ratio("blue", "#FFFFFF")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid color must be rejected")


def test_unknown_theme_is_rejected():
    try:
        palette_for("neon")
    except ValueError as error:
        assert "system" in str(error)
    else:
        raise AssertionError("unknown themes must be rejected")


def test_preferred_theme_loader_returns_supported_mode():
    assert load_preferred_theme() in {"system", "light", "dark"}
