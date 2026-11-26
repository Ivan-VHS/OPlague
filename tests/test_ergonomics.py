from oplage_app import TEXT_SIZE_MAX, TEXT_SIZE_MIN, bounded_text_size


def test_report_text_zoom_stays_within_readable_limits():
    assert bounded_text_size(10, 1) == 11
    assert bounded_text_size(10, -1) == 9
    assert bounded_text_size(TEXT_SIZE_MAX, 1) == TEXT_SIZE_MAX
    assert bounded_text_size(TEXT_SIZE_MIN, -1) == TEXT_SIZE_MIN


def test_report_text_zoom_clamps_large_steps():
    assert bounded_text_size(10, 100) == TEXT_SIZE_MAX
    assert bounded_text_size(10, -100) == TEXT_SIZE_MIN
