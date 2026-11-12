"""The S2 Pro sentence join and level match: one gain per sentence, 0.4 s pauses, a peak at 0.98."""
import numpy as np

from speak_s2pro import MAX_BOOST_DB, MAX_PARA_SPREAD_DB, PAUSE_SECONDS, PEAK_LIMIT, level_and_join, voiced_db

RATE = 16000


def tone(amplitude: float, seconds: float = 1.0) -> np.ndarray:
    """A constant tone of `amplitude` for `seconds`."""
    return np.full(int(RATE * seconds), amplitude, dtype=np.float32)


def piece_level(joined: np.ndarray, index: int, size: int) -> float:
    """Voiced level of piece `index` in a joined signal of equal-size pieces."""
    step = size + int(PAUSE_SECONDS * RATE)
    return voiced_db(joined[index * step:index * step + size], RATE)


def test_voiced_db_measures_a_constant_tone():
    assert abs(voiced_db(tone(0.1), RATE) - (-20.0)) < 0.01


def test_voiced_db_ignores_pauses_below_the_floor():
    piece = np.concatenate([np.zeros(RATE // 2, dtype=np.float32), tone(0.1, 0.5)])
    assert abs(voiced_db(piece, RATE) - (-20.0)) < 0.01


def test_level_and_join_matches_every_piece_to_the_median_voiced_level():
    pieces = [tone(0.07), tone(0.1), tone(0.09)]  # within the boost cap of the median (0.09)
    joined = level_and_join(pieces, RATE, [1, 1, 1])
    measured = [piece_level(joined, i, len(pieces[0])) for i in range(len(pieces))]
    assert max(measured) - min(measured) < 0.1
    assert abs(measured[0] - voiced_db(pieces[2], RATE)) < 0.1  # the median piece keeps its level
    assert len(joined) == len(pieces) * len(pieces[0]) + (len(pieces) - 1) * int(PAUSE_SECONDS * RATE)


def test_level_and_join_caps_a_positive_gain_but_not_an_attenuation():
    pieces = [tone(0.01), tone(1.0), tone(0.1)]  # each alone in its paragraph, so no spread to trim
    joined = level_and_join(pieces, RATE, [1, 2, 3])
    quiet = piece_level(joined, 0, len(pieces[0]))
    loud = piece_level(joined, 1, len(pieces[0]))
    assert abs(quiet - (voiced_db(pieces[0], RATE) + MAX_BOOST_DB)) < 0.1  # +20 dB wanted, +3 dB applied
    assert abs(loud - voiced_db(pieces[2], RATE)) < 0.1  # -20 dB wanted, applied in full


def test_level_and_join_trims_the_loud_pieces_of_a_capped_paragraph():
    quiet = tone(0.1 * 10 ** (-5 / 20))  # 5 dB below the median, so its +5 dB gain is held at +3 dB
    pieces = [tone(0.1), quiet, tone(0.1)]
    joined = level_and_join(pieces, RATE, [1, 1, 2])
    quiet_level = piece_level(joined, 1, len(pieces[0]))
    trimmed_level = piece_level(joined, 0, len(pieces[0]))
    other_paragraph = piece_level(joined, 2, len(pieces[0]))
    assert abs(quiet_level - (voiced_db(quiet, RATE) + MAX_BOOST_DB)) < 0.1  # the quiet piece keeps its +3 dB
    assert abs((trimmed_level - quiet_level) - MAX_PARA_SPREAD_DB) < 0.1  # its mate is trimmed to the spread
    assert abs(other_paragraph - voiced_db(pieces[2], RATE)) < 0.1  # another paragraph is untouched


def test_level_and_join_holds_the_peak_at_the_limit():
    joined = level_and_join([tone(0.5), tone(2.0)], RATE, [1, 2])
    assert abs(np.abs(joined).max() - PEAK_LIMIT) < 1e-6
