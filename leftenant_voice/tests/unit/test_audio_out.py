"""The MP3 writer's headroom: a peak above -1 dBFS comes down to it, and a quieter signal is not raised."""
import numpy as np

from audio_out import MP3_PEAK, with_mp3_headroom


def test_a_peak_above_the_limit_is_scaled_down_to_it():
    samples = with_mp3_headroom(np.array([0.98, -0.5, 0.2], dtype=np.float32))
    assert abs(float(np.abs(samples).max()) - MP3_PEAK) < 1e-6


def test_audio_below_the_limit_is_unchanged():
    audio = np.array([0.2, -0.1], dtype=np.float32)
    assert np.array_equal(with_mp3_headroom(audio), audio)
