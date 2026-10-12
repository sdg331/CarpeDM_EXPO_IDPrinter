import numpy as np

from scripts.evaluate_lfw import summarize


def test_summary_keeps_unselected_characters_and_counts_close_margins():
    scores = np.array([[.5, .49, .1], [.1, .6, .2], [.7, .1, .2]])
    result = summarize(scores, ["char_01", "char_02", "char_03"])
    assert result["counts"] == {"char_01": 2, "char_02": 1, "char_03": 0}
    assert result["used"] == 2
    assert result["fragile_count"] == 1
    assert result["largest_share"] == 2 / 3
